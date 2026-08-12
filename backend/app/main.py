from fastapi import FastAPI
from app.api.meeting import router as meeting_router

app = FastAPI(
    title="MeetIQ API",
    description="Backend API for the MeetIQ meeting intelligence platform.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "MeetIQ API is running"}

app.include_router(meeting_router)