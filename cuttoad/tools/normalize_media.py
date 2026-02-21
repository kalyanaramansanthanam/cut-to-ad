from __future__ import annotations

import subprocess
from pathlib import Path

from cuttoad.config import Config


def normalize_clips(clip_paths: list[Path], run_dir: Path, cfg: Config) -> list[Path]:
    if not cfg.ffmpeg_path:
        raise RuntimeError("ffmpeg is required for clip normalization.")
    normalized_dir = run_dir / "normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    normalized_paths: list[Path] = []
    for idx, clip_path in enumerate(clip_paths, start=1):
        out_path = normalized_dir / f"clip_{idx:02d}.mp4"
        cmd = [
            cfg.ffmpeg_path,
            "-y",
            "-i",
            str(clip_path),
            "-vf",
            "fps=30,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(out_path),
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg normalization failed: {result.stderr.strip()}")
        normalized_paths.append(out_path)
    return normalized_paths
