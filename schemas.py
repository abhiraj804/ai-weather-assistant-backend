from pydantic import BaseModel
from typing import Optional, List

# Frontend sends this to get a response
class ChatRequest(BaseModel):
    user_message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    chat_summary: Optional[str] = "No previous context."
    theme: Optional[str] = "General"

# Frontend sends this to get Audio
class TTSRequest(BaseModel):
    text: str
    language: str  # "en" or "ja"

# Backend sends this back to Frontend (The LLM Structure)
class ChatResponse(BaseModel):
    english_text: str
    japanese_text: str
    summary: str
    hex_color: str
    avatar_state: str
    location_name: str