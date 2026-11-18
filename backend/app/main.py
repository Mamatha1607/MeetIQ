from fastapi import FastAPI
from app.api.meeting import router as meeting_router
from app.api.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="MeetIQ API",
    description="Backend API for the MeetIQ meeting intelligence platform.",
    version="0.1.0",
)
# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST","PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "MeetIQ API is running"}

app.include_router(meeting_router)
app.include_router(auth_router)