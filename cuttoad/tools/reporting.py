from __future__ import annotations

from pathlib import Path
from typing import Any

from cuttoad.io_utils import atomic_write_json
from cuttoad.schema_validation import validate_artifact


def write_report(
    run_dir: Path,
    status: str,
    final_video: str | None,
    warnings: list[str],
    validation: dict[str, Any],
) -> dict[str, Any]:
    report = {
        "schema_version": "v1",
        "status": status,
        "final_video": final_video,
        "warnings": warnings,
        "validation_score": validation.get("total_score"),
    }
    validate_artifact("report.v1.schema.json", report)
    atomic_write_json(run_dir / "report.v1.json", report)
    return report
