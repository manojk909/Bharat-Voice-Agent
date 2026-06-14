import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

async def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set!")
        return

    print("Using GEMINI_API_KEY:", api_key[:10] + "...")
    genai.configure(api_key=api_key)
    
    try:
        print("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name}")
    except Exception as e:
        print("\n--- ERROR LISTING MODELS ---")
        print(str(e))
        print("----------------------------")

if __name__ == "__main__":
    asyncio.run(test_gemini())
