import os
import json
from google.cloud import speech, texttospeech
from pydub import AudioSegment
import io
import traceback

# Setup Google Cloud credentials
# If GOOGLE_APPLICATION_CREDENTIALS contains JSON string instead of file path,
# write it to a temporary file
creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if creds_env:
    if creds_env.startswith("{"):
        # It's JSON content, not a file path - write to temp file
        creds_path = "/tmp/gcloud_credentials.json"
        try:
            # Validate JSON first
            json.loads(creds_env)
            with open(creds_path, "w") as f:
                f.write(creds_env)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
            print(f"✅ Google Cloud credentials written to {creds_path}")
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS: {e}")
    else:
        print(f"✅ Using credentials file: {creds_env}")
else:
    print("⚠️ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set!")

# Setup clients (Auth is handled via GOOGLE_APPLICATION_CREDENTIALS env var)
stt_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()

# In backend/services/audio_service.py

async def transcribe_audio(file_bytes: bytes) -> str:
    try:
        # On Windows development, use local ffmpeg.exe if available
        # On Linux (Render/Production), it uses system-installed ffmpeg
        if os.path.exists("ffmpeg.exe"):
             AudioSegment.converter = os.path.abspath("ffmpeg.exe")
        
        # 1. Convert WebM -> WAV (16-bit, 16kHz, Mono)
        audio = AudioSegment.from_file(io.BytesIO(file_bytes))
        
        # --- THE FIX IS IN THIS LINE BELOW ---
        # .set_sample_width(2) forces it to be 16-bit (2 bytes)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        # -------------------------------------

        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_content = wav_io.getvalue()

        # 2. Call Google Cloud STT
        audio_api = speech.RecognitionAudio(content=wav_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="ja-JP", 
            alternative_language_codes=["en-US"],
            enable_automatic_punctuation=True,
        )

        response = stt_client.recognize(config=config, audio=audio_api)
        
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
            
        return transcript

    except Exception as e:
        print("TRANSCRIPTION ERROR:", e)
        # return empty string so app doesn't crash, or raise e if you prefer
        return ""

async def generate_tts(text: str, lang: str):
    """Generates MP3 audio from text"""
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Select voice based on language
        lang_code = "ja-JP" if lang == "ja" else "en-US"
        voice_name = "ja-JP-Neural2-B" if lang == "ja" else "en-US-Neural2-F" # Neural voices sound better

        voice = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content
    
    except Exception as e:
        print(f"TTS ERROR: {e}")
        raise e  # Re-raise so the endpoint returns proper error