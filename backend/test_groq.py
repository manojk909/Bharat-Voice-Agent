import asyncio
import os
from dotenv import load_dotenv
from app.services.ai.gemini import gemini_client

load_dotenv()

async def test_groq():
    transcript = "मेरा नाम त्रिवेद है, मैं एक फार्मर हूँ, मेरे पास 3 एकड़ का ज़मीन है, मैं महाराष्ट्र से बिलोंग करता हूँ, तो मेरे रिलेटेड कोई भी गवर्नमेंट स्कीम है तो दिखाना।"
    print(f"Testing Groq extraction with transcript:\n'{transcript}'\n")
    
    # 1. Test profile extraction
    profile = await gemini_client.extract_profile(transcript)
    print("--- EXTRACTED PROFILE RESULT ---")
    print(profile)
    print("--------------------------------")
    
    # 2. Test keyword generation
    keywords = await gemini_client.generate_keywords(profile)
    print("\n--- GENERATED KEYWORDS ---")
    print(keywords)
    print("--------------------------")

if __name__ == "__main__":
    asyncio.run(test_groq())
