
"""
AI meeting summarization service.

Responsibilities:
1. Send meeting transcripts to Ollama.
2. Generate structured meeting insights.
3. Validate the model's JSON response.
"""

import json

import httpx
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    task: str
    assignee: str | None = None
    due_date: str | None = None


class MeetingInsights(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


def generate_meeting_insights(transcript: str) -> MeetingInsights:
    """Generate structured insights from a meeting transcript."""

    if not transcript.strip():
        raise ValueError("Cannot summarize an empty transcript")

    prompt = f"""
Analyze the following meeting transcript.

Return:
1. A concise meeting summary.
2. Important discussion points.
3. Decisions made.
4. Action items with assignees and deadlines.

Rules:
- Use only information present in the transcript.
- Do not invent decisions, tasks, names, or dates.
- Use null for unknown assignees or deadlines.
- Return structured JSON matching the requested schema.

TRANSCRIPT:
{transcript}
"""

    response = httpx.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:7b",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": MeetingInsights.model_json_schema(),
            "options": {"temperature": 0},
        },
        timeout=httpx.Timeout(
        connect=10.0,
        read=900.0,
        write=30.0,
        pool=10.0,
    ),
    )

    response.raise_for_status()

    content = response.json()["message"]["content"]

    return MeetingInsights.model_validate_json(content)
