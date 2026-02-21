from __future__ import annotations

from pathlib import Path
from typing import Any

from cuttoad.io_utils import atomic_write_json
from cuttoad.schema_validation import validate_artifact


def validate_script(
    script: dict[str, Any],
    product: str,
    run_dir: Path,
    min_total_score: int = 28,
) -> dict[str, Any]:
    scenes = script.get("scenes", [])
    total_duration = sum(scene.get("duration_sec", 0) for scene in scenes)
    has_cta = any(scene.get("cta") for scene in scenes)
    mentions_product = any(product.lower() in scene.get("description", "").lower() for scene in scenes)

    errors: list[str] = []
    if not 18 <= total_duration <= 24:
        errors.append("Total planned duration must be between 18 and 24 seconds.")
    if not has_cta:
        errors.append("Script must include CTA in at least one scene.")
    if not mentions_product:
        errors.append("Script must mention product in scene descriptions.")

    breakdown = {
        "style": 7,
        "product": 8 if mentions_product else 3,
        "audience": 7,
        "flow": 7 if not errors else 4,
    }
    total_score = int(sum(breakdown.values()))
    passed = total_score >= min_total_score and not errors

    validation = {
        "schema_version": "v1",
        "passed": passed,
        "total_score": total_score,
        "breakdown": breakdown,
        "errors": errors,
        "feedback": "Revise scene transitions and CTA clarity." if not passed else "",
    }
    validate_artifact("validation.v1.schema.json", validation)
    atomic_write_json(run_dir / "validation.v1.json", validation)
    return validation
