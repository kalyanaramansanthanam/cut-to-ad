from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from cuttoad.config import Config


def _generate_placeholder_clip(
    output_path: Path,
    duration_sec: float,
    cfg: Config,
    width: int = 720,
    height: int = 1280,
) -> None:
    if not cfg.ffmpeg_path:
        raise RuntimeError("ffmpeg is required to create placeholder clips.")
    cmd = [
        cfg.ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s={width}x{height}:d={duration_sec}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg clip generation failed: {result.stderr.strip()}")


def generate_all_clips(
    script: dict[str, Any],
    run_dir: Path,
    cfg: Config,
    max_workers: int = 4,
) -> list[Path]:
    clips_dir = run_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    scenes = script.get("scenes", [])
    out_paths: list[Path] = []
    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for scene in scenes:
            clip_path = clips_dir / f"clip_{scene['index']:02d}.mp4"
            out_paths.append(clip_path)
            futures.append(
                executor.submit(
                    _generate_placeholder_clip,
                    clip_path,
                    float(scene.get("duration_sec", 5.0)),
                    cfg,
                )
            )
        for future in as_completed(futures):
            future.result()
    return out_paths
