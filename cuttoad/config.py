from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    output_root: Path
    poll_interval_seconds: int
    max_poll_attempts: int
    max_script_iterations: int
    default_scenes: int
    ffmpeg_path: str | None
    ffprobe_path: str | None
    google_api_key: str | None
    minimax_api_key: str | None
    aws_region: str
    claude_model_id: str
    gemini_model_id: str


def load_config() -> Config:
    load_dotenv()
    return Config(
        output_root=Path(os.getenv("CUTTOAD_OUTPUT_DIR", "output")).resolve(),
        poll_interval_seconds=int(os.getenv("CUTTOAD_POLL_INTERVAL_SECONDS", "10")),
        max_poll_attempts=int(os.getenv("CUTTOAD_MAX_POLL_ATTEMPTS", "60")),
        max_script_iterations=int(os.getenv("CUTTOAD_MAX_SCRIPT_ITERATIONS", "3")),
        default_scenes=int(os.getenv("CUTTOAD_DEFAULT_SCENES", "4")),
        ffmpeg_path=shutil.which("ffmpeg"),
        ffprobe_path=shutil.which("ffprobe"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        minimax_api_key=os.getenv("MINIMAX_API_KEY"),
        aws_region=os.getenv("AWS_REGION", "us-west-2"),
        claude_model_id=os.getenv("CLAUDE_MODEL_ID", "anthropic.claude-sonnet-4-5"),
        gemini_model_id=os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash"),
    )
