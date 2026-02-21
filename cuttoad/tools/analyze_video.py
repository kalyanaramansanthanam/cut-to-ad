from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from cuttoad.config import Config
from cuttoad.io_utils import atomic_write_json
from cuttoad.schema_validation import validate_artifact


def _probe_duration_seconds(video_path: Path, cfg: Config) -> float:
    if not cfg.ffprobe_path:
        return 20.0
    cmd = [
        cfg.ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return 20.0
    try:
        return max(float(result.stdout.strip()), 1.0)
    except ValueError:
        return 20.0


def analyze_video(
    video_path: Path,
    run_dir: Path,
    cfg: Config,
    dry_run: bool,
    num_scenes: int = 4,
) -> dict[str, Any]:
    if not video_path.exists():
        raise FileNotFoundError(f"Input video does not exist: {video_path}")
    if num_scenes < 1:
        raise ValueError("num_scenes must be >= 1")
    duration = _probe_duration_seconds(video_path, cfg)
    scene_duration = round(duration / float(num_scenes), 2)
    analysis = {
        "schema_version": "v1",
        "source_video": str(video_path),
        "mode": "stub" if dry_run or not cfg.google_api_key else "provider-pending",
        "visual_style": "cinematic lifestyle",
        "mood": "optimistic",
        "pacing": "medium",
        "lighting": "natural",
        "scenes": [
            {
                "index": idx + 1,
                "timestamp_start_sec": round(idx * scene_duration, 2),
                "timestamp_end_sec": round((idx + 1) * scene_duration, 2),
                "description": f"Scene {idx + 1} from source video style references.",
            }
            for idx in range(num_scenes)
        ],
    }
    validate_artifact("analysis.v1.schema.json", analysis)
    atomic_write_json(run_dir / "analysis.v1.json", analysis)
    return analysis
