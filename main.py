from dotenv import load_dotenv
load_dotenv()

import json
import re
import uvicorn
import asyncio
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response


from schemas import ChatRequest, ChatResponse, TTSRequest
from services.location_service import resolve_coordinates, get_location_name, get_coordinates_from_city
from services.llm_service import chat_with_gemini, detect_target_location
from services.audio_service import transcribe_audio, generate_tts


def extract_location_from_summary(summary: str) -> str:
    """Extract location from chat summary, e.g., 'In Tokyo, ...' -> 'Tokyo'"""
    if not summary:
        return None
    match = re.search(r'In\s+([^,(]+)', summary)
    if match:
        return match.group(1).strip()
    return None


# Background task for keep-alive
async def keepalive_task():
    """Background task that keeps the service active and Gemini warm"""
    await asyncio.sleep(60)  # Wait 1 minute before starting
    
    gemini_counter = 0
    
    while True:
        try:
            # Self-ping every minute to keep Render awake
            print("🔄 Self-ping to stay active...")
            
            # Every 10 minutes, also ping Gemini to keep it warm
            if gemini_counter >= 10:
                print("🔄 Pinging Gemini API...")
                await chat_with_gemini(
                    message="ping",
                    history_summary="",
                    city_name="Tokyo",
                    lat=35.6762,
                    lon=139.6503,
                    theme="friendly"
                )
                print("✅ Gemini keep-alive successful")
                gemini_counter = 0
            else:
                print("✅ Self-ping successful")
                gemini_counter += 1
            
        except Exception as e:
            print(f"⚠️ Keep-alive failed: {e}")
        
        # Wait 1 minute before next ping
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to run background tasks"""
    # Start the keep-alive task
    task = asyncio.create_task(keepalive_task())
    print("🚀 Keep-alive background task started")
    yield
    # Cleanup on shutdown
    task.cancel()
    print("🛑 Keep-alive background task stopped")


app = FastAPI(lifespan=lifespan)

# Allow CORS for React (Vite usually runs on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all. Lock down for prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "TenkiGuide Backend is Running"}

@app.get("/keepalive")
async def keepalive():
    """Health check endpoint that also pings Gemini to keep it active"""
    try:
        # Simple ping to Gemini to keep it warm
        test_response = await chat_with_gemini(
            message="ping",
            history_summary="",
            city_name="Tokyo",
            lat=35.6762,
            lon=139.6503,
            theme="friendly"
        )
        return {
            "status": "ok",
            "message": "Backend and Gemini API are active",
            "gemini_responsive": True
        }
    except Exception as e:
        return {
            "status": "ok",
            "message": "Backend is active",
            "gemini_responsive": False,
            "error": str(e)
        }

@app.get("/location")
async def location_endpoint(lat: float = Query(...), lon: float = Query(...)):
    """Get location name from latitude and longitude"""
    try:
        # Use the same logic as in chat endpoint
        client_ip = None  # No IP for this endpoint
        resolved_lat, resolved_lon = resolve_coordinates(lat, lon, client_ip)
        location_name = await get_location_name(resolved_lat, resolved_lon)
        return {"location_name": location_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """Receives Audio Blob -> Returns Text"""
    try:
        content = await file.read()
        text = await transcribe_audio(content)
        return {"transcript": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, req: Request):
    
    # Priority 1: Check if user explicitly mentioned a city in current message
    target_city = await detect_target_location(request.user_message)
    
    if target_city:
        print(f"🎯 User explicitly mentioned: {target_city}")
        new_lat, new_lon, new_name = await get_coordinates_from_city(target_city)
        if new_lat is not None:
            lat = new_lat
            lon = new_lon
            location_name = new_name
        else:
            # Fallback if city lookup fails
            client_ip = req.client.host
            lat, lon = resolve_coordinates(request.latitude, request.longitude, client_ip)
            location_name = await get_location_name(lat, lon)
    else:
        # Priority 2: Check summary for previous location (context continuity)
        summary_location = extract_location_from_summary(request.chat_summary)
        if summary_location:
            print(f"📝 Using location from summary: {summary_location}")
            new_lat, new_lon, new_name = await get_coordinates_from_city(summary_location)
            if new_lat is not None:
                lat = new_lat
                lon = new_lon
                location_name = new_name
            else:
                # Fallback if summary city lookup fails
                client_ip = req.client.host
                lat, lon = resolve_coordinates(request.latitude, request.longitude, client_ip)
                location_name = await get_location_name(lat, lon)
        else:
            # Priority 3: Fall back to GPS/IP location (initial default)
            print(f"📍 Using GPS/IP location")
            client_ip = req.client.host
            lat, lon = resolve_coordinates(request.latitude, request.longitude, client_ip)
            location_name = await get_location_name(lat, lon)
            
    # 3. Call Gemini (Now passing the CORRECT location's coords)
    raw_response = await chat_with_gemini(
        message=request.user_message,
        history_summary=request.chat_summary,
        city_name=location_name, # Passed to prompt
        lat=lat,                 # Passed to weather service
        lon=lon,                 # Passed to weather service
        theme=request.theme
    )
    
    # 4. Parse and Return
    try:
        data = json.loads(raw_response)
        data["location_name"] = location_name 
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response")

@app.post("/tts")
async def tts_endpoint(request: TTSRequest):
    """Generates Audio on demand"""
    try:
        audio_content = await generate_tts(request.text, request.language)
        return Response(content=audio_content, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)