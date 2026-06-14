from app.core.database import schemes_collection
from app.services.ai.gemini import gemini_client
import json

class RAGService:
    async def discover_schemes(self, profile: dict) -> list[dict]:
        """
        Discovers relevant schemes for a user profile by performing a hybrid text search 
        on MongoDB followed by a Gemini-based eligibility evaluation.
        """
        try:
            # 1. Generate search keywords using Gemini based on the user's profile
            keywords = await gemini_client.generate_keywords(profile)
            search_query = " ".join(keywords)
            print(f"RAG search query generated: '{search_query}'")

            # 2. Fetch candidates from MongoDB using Text Index
            candidates = []
            cursor = schemes_collection.find(
                {"$text": {"$search": search_query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(10)
            
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                candidates.append(doc)

            # Fallback: if no text index match, pull all active schemes to evaluate
            if not candidates:
                print("No text index matches. Falling back to default list.")
                cursor = schemes_collection.find().limit(10)
                async for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    candidates.append(doc)

            print(f"Found {len(candidates)} candidate schemes for evaluation.")

            # 3. Evaluate eligibility for all candidates in a single batch call
            eligible_schemes = []
            evaluations = await gemini_client.evaluate_multiple_eligibility(profile, candidates)
            
            # Create a lookup map for the evaluation results
            eval_map = {ev.get("id"): ev for ev in evaluations if isinstance(ev, dict) and ev.get("id")}
            
            for candidate in candidates:
                cand_id = candidate.get("id")
                if cand_id in eval_map:
                    ev = eval_map[cand_id]
                    if ev.get("eligible"):
                        eligible_schemes.append({
                            "id": cand_id,
                            "title": candidate.get("title"),
                            "description": candidate.get("description"),
                            "benefits": candidate.get("benefits"),
                            "required_documents": candidate.get("required_documents", []),
                            "application_deadline": candidate.get("application_deadline", "Open"),
                            "source_url": candidate.get("source_url", ""),
                            "eligibility_reason": ev.get("reason", "Eligible"),
                            "confidence": ev.get("confidence", 100)
                        })

            # Sort by confidence descending
            eligible_schemes.sort(key=lambda x: x["confidence"], reverse=True)
            return eligible_schemes

        except Exception as e:
            print("Error in RAG discover_schemes:", e)
            return []

rag_service = RAGService()
