
# TenkiGuide - Backend API

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal?logo=fastapi)
![Render](https://img.shields.io/badge/Deployment-Render-black?logo=render)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5-orange?logo=google)

The backend service for **TenkiGuide**, a conversational AI weather assistant. This API handles natural language understanding, real-time weather aggregation, and bi-directional audio processing (Speech-to-Text and Text-to-Speech).

> **Note:** This service acts as the brain for the [AI Weather Assistant Frontend](https://github.com/abhiraj804/ai-weather-assistant-frontend).

---

## 🚀 Features

* **⚡ High-Performance API:** Built on **FastAPI** for asynchronous request handling and automatic validation.
* **🧠 Context-Aware AI:** Integrates **Google Gemini 2.5 Flash Lite** to generate persona-based responses with strict JSON formatting.
* **🎤 Audio Processing Pipeline:**
    * Transcodes incoming WebM audio (from browsers) to WAV using **FFmpeg**.
    * Interacts with **Google Cloud STT & TTS** APIs for enterprise-grade voice support.
* **🌦️ Weather Integration:** Fetches real-time data from Open-Meteo (no API key required).
* **🔋 Zero-Config Keep-Alive:** Includes an internal background task to prevent cold starts on serverless platforms (specifically Render Free Tier).

## 🛠️ Prerequisites

To run this server locally, you will need:

* **Python 3.11+**
* **FFmpeg** (Required for audio transcoding):
    * *Mac:* `brew install ffmpeg`
    * *Windows:* Download `ffmpeg.exe` and add it to your PATH (or place it in the root folder).
    * *Linux:* `sudo apt-get install ffmpeg`
* **Google Cloud Project** with the following APIs enabled:
    * Cloud Speech-to-Text API
    * Cloud Text-to-Speech API
* **Gemini API Key** (via Google AI Studio)

## 💻 Local Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/abhiraj804/ai-weather-assistant-backend.git
    cd ai-weather-assistant-backend
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    
    # Mac/Linux
    source venv/bin/activate
    
    # Windows
    venv\Scripts\activate
    ```

3.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration (.env)**
    Create a `.env` file in the root directory:

    ```env
    # Google AI Studio Key
    GEMINI_API_KEY=your_gemini_api_key_here

    # Google Cloud Credentials
    # Option A: Path to your JSON file (Standard for local dev)
    GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
    
    # Option B: JSON Content string (Useful for cloud deployment)
    # GOOGLE_APPLICATION_CREDENTIALS='{"type": "service_account", ...}'
    ```

## ▶️ Running the Server

Start the development server with hot-reload enabled:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### 📚 API Documentation

Once the server is running, you can access the interactive documentation:

  * **Swagger UI:** `http://localhost:8000/docs`
  * **ReDoc:** `http://localhost:8000/redoc`

## ☁️ Deployment (Render)

This repository is strictly configured for **Render's Native Python Environment** (no Dockerfile required).

1.  **Infrastructure as Code:**
    The `render.yaml` file tells Render to use the `python` environment.

2.  **Custom Build Script (`build.sh`):**
    Since the `pydub` library requires FFmpeg, this project uses a custom build script.
    *   It automatically runs `apt-get install ffmpeg`.
    *   Then it runs `pip install -r requirements.txt`.

3.  **Environment Variables:**
    When deploying to Render, ensure `GEMINI_API_KEY` and `GOOGLE_APPLICATION_CREDENTIALS` are set in your dashboard.

    *Tip: For `GOOGLE_APPLICATION_CREDENTIALS`, copy the entire content of your JSON key file and paste it as the environment variable value.*

## 🧪 Testing Endpoints

You can verify the setup using cURL:

**1. Chat (Text)**
*(Includes coordinates to prevent IP-based fallback during local development)*
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "user_message": "What should I wear?", 
       "theme": "Fashion",
       "latitude": 35.6762,
       "longitude": 139.6503
     }'
```

**2. Health Check**

```bash
curl http://localhost:8000/keepalive
```

**3. Text-to-Speech (TTS)**
Generates an MP3 file from text.

```bash
curl -X POST "http://localhost:8000/tts" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello world", "language": "en"}' \
     --output output.mp3
     ```

**4. Speech-to-Text (Transcribe)**
Requires a valid audio file (WebM or WAV).

```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/audio.webm"
     ```

**5. Location Lookup**
Resolves coordinates to a city name.

```bash
curl "http://localhost:8000/location?lat=35.6762&lon=139.6503"
     ```

     
## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```