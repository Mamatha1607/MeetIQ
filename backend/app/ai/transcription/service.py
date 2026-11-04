
"""
Transcription service powered by OpenAI Whisper.

Responsibilities:
1. Load and cache the Whisper model.
2. Convert audio/video recordings into text.
3. Measure model loading and transcription time.
4. Print debugging information.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import time

import whisper


# --------------------------------------------------
# STEP 1: Define the transcription result
# --------------------------------------------------

@dataclass
class TranscriptionResult:
    """Standard result returned by our transcription service."""

    text: str
    language: str | None = None


# --------------------------------------------------
# STEP 2: Load and cache the Whisper model
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_whisper_model():
    """
    Load Whisper once and reuse the model for subsequent requests.
    """

    print("[Whisper] Starting model loading...", flush=True)

    # Start measuring model loading time.
    start_time = time.perf_counter()

    # Load the Whisper base model.
    model = whisper.load_model("base")

    # Calculate model loading duration.
    elapsed = time.perf_counter() - start_time

    print(
        f"[Whisper] Model loading took {elapsed:.2f} seconds",
        flush=True,
    )

    return model


# --------------------------------------------------
# STEP 3: Transcribe an audio/video recording
# --------------------------------------------------

def transcribe_audio(file_path: Path) -> TranscriptionResult:
    """
    Convert an uploaded recording into text
    and measure processing performance.
    """

    # Confirm that this function is being executed.
    print(
        "DEBUG: TRANSCRIPTION SERVICE EXECUTED",
        flush=True,
    )

    # Check whether the uploaded recording exists.
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Meeting recording not found: {file_path}"
        )

    print(
        f"[Whisper] Processing file: {file_path.name}",
        flush=True,
    )

    # Measure model loading or retrieval time.
    model_start = time.perf_counter()

    model = get_whisper_model()

    model_time = time.perf_counter() - model_start

    print(
        f"[Whisper] Model retrieval: {model_time:.2f}s",
        flush=True,
    )

    # Start measuring actual transcription time.
    transcription_start = time.perf_counter()

    print(
        "[Whisper] Transcription started...",
        flush=True,
    )

    # Perform speech-to-text transcription.
    result = model.transcribe(
        str(file_path),
        fp16=False,
    )

    # Calculate transcription duration.
    transcription_time = (
        time.perf_counter() - transcription_start
    )

    print(
        f"[Whisper] Transcription: {transcription_time:.2f}s",
        flush=True,
    )

    print(
        "[Whisper] Transcription completed successfully.",
        flush=True,
    )

    # Return the transcript and detected language.
    return TranscriptionResult(
        text=result["text"].strip(),
        language=result.get("language"),
    )
