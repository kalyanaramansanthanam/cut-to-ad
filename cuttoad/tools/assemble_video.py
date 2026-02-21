from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from cuttoad.config import Config


def assemble_video(clip_paths: list[Path], run_dir: Path, cfg: Config) -> Path:
    if not cfg.ffmpeg_path:
        raise RuntimeError("ffmpeg is required for assembly.")
    concat_list_path = run_dir / "concat_list.txt"
    with concat_list_path.open("w", encoding="utf-8") as handle:
        for clip_path in clip_paths:
            handle.write(f"file '{clip_path.resolve()}'\n")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = run_dir / f"cuttoad_ad_{timestamp}.mp4"
    cmd = [
        cfg.ffmpeg_path,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list_path),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg assembly failed: {result.stderr.strip()}")
    return output_path
