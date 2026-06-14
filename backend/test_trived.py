import asyncio
import os
from dotenv import load_dotenv
from app.core.database import schemes_collection
from app.services.ai.gemini import gemini_client
import json

load_dotenv()

async def test_trived_eval():
    profile = {
        "name": "त्रिवेद",
        "age": None,
        "gender": None,
        "state": "महाराष्ट्र",
        "district": None,
        "occupation": "फार्मर",
        "education": None,
        "annual_income": None,
        "caste_category": None,
        "parent_occupation": None,
        "disability_status": None
    }
    
    candidates = []
    cursor = schemes_collection.find().limit(10)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        candidates.append(doc)

    print("Candidates loaded:")
    for c in candidates:
        print(f"- {c['title']}")
        
    print("\nSending all candidates to Groq (Llama 3.3) for evaluation...")
    evaluations = await gemini_client.evaluate_multiple_eligibility(profile, candidates)
    print("\n--- RAW EVALUATION ARRAY FROM LLM ---")
    print(json.dumps(evaluations, indent=2, ensure_ascii=False))
    print("--------------------------------------")

if __name__ == "__main__":
    asyncio.run(test_trived_eval())
