from __future__ import annotations

from pathlib import Path
from typing import Any

from cuttoad.io_utils import atomic_write_json
from cuttoad.schema_validation import validate_artifact


def generate_script(
    analysis: dict[str, Any],
    product: str,
    audience: str,
    run_dir: Path,
    num_scenes: int = 4,
    feedback: str = "",
) -> dict[str, Any]:
    if num_scenes < 1:
        raise ValueError("num_scenes must be >= 1")
    scene_duration = round(20.0 / float(num_scenes), 2)
    scenes = []
    for idx in range(num_scenes):
        scenes.append(
            {
                "index": idx + 1,
                "duration_sec": scene_duration,
                "description": (
                    f"Scene {idx + 1}: {analysis['visual_style']} tone, feature {product} naturally "
                    f"for {audience}. {feedback}".strip()
                ),
                "camera": "steady close + medium cut",
                "mood": analysis["mood"],
                "cta": idx == num_scenes - 1,
            }
        )
    script = {
        "schema_version": "v1",
        "rationale": f"Optimized for {audience} with natural {product} integration.",
        "scenes": scenes,
    }
    validate_artifact("script.v1.schema.json", script)
    atomic_write_json(run_dir / "script.v1.json", script)
    return script
