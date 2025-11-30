from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
import os


api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: API Key not found in .env")
else:
    genai.configure(api_key=api_key)
    print("Checking available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")