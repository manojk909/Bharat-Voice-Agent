from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as v1_router
from app.core.config import settings

app = FastAPI(
    title="Bharat Voice Agent API",
    description="Backend API for Bharat Voice Agent",
    version="1.0.0"
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    from app.core.database import init_db
    from app.services.scraper import seed_all_schemes
    await init_db()
    await seed_all_schemes()

@app.get("/health")
def health_check():
    return {"status": "ok"}
