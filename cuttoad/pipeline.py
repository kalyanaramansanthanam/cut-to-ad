from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cuttoad.agents.scriptwriter import generate_script
from cuttoad.agents.validator import validate_script
from cuttoad.config import Config
from cuttoad.io_utils import atomic_write_json
from cuttoad.schema_validation import validate_artifact
from cuttoad.tools.analyze_video import analyze_video
from cuttoad.tools.assemble_video import assemble_video
from cuttoad.tools.generate_clips import generate_all_clips
from cuttoad.tools.normalize_media import normalize_clips
from cuttoad.tools.reporting import write_report


def make_run_id(explicit_run_id: str | None) -> str:
    if explicit_run_id:
        return explicit_run_id
    return f"run_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"


def update_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    validate_artifact("manifest.v1.schema.json", manifest)
    atomic_write_json(run_dir / "manifest.json", manifest)


def run_pipeline(
    cfg: Config,
    video_path: Path,
    product: str,
    audience: str,
    run_id: str | None,
    max_scenes: int,
) -> Path:
    resolved_run_id = make_run_id(run_id)
    run_dir = cfg.output_root / resolved_run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schema_version": "v1",
        "run_id": resolved_run_id,
        "status": "running",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input": {
            "video_path": str(video_path.resolve()),
            "product": product,
            "audience": audience,
            "max_scenes": max_scenes,
        },
        "steps": {
            "analyze": "pending",
            "script": "pending",
            "validate": "pending",
            "generate": "pending",
            "assemble": "pending",
            "report": "pending",
        },
        "warnings": [],
    }
    update_manifest(run_dir, manifest)

    analysis = analyze_video(video_path, run_dir, cfg, dry_run=True)
    manifest["steps"]["analyze"] = "completed"
    update_manifest(run_dir, manifest)

    feedback = ""
    script = {}
    validation = {}
    for _attempt in range(cfg.max_script_iterations):
        script = generate_script(
            analysis=analysis,
            product=product,
            audience=audience,
            run_dir=run_dir,
            num_scenes=max_scenes,
            feedback=feedback,
        )
        manifest["steps"]["script"] = "completed"
        validation = validate_script(script=script, product=product, run_dir=run_dir)
        if validation["passed"]:
            manifest["steps"]["validate"] = "completed"
            break
        feedback = validation.get("feedback", "")
        manifest["steps"]["validate"] = "retry"
    else:
        manifest["status"] = "failed"
        manifest["warnings"].append("Script did not pass validation after max retries.")
        update_manifest(run_dir, manifest)
        write_report(run_dir, "failed", None, manifest["warnings"], validation)
        raise RuntimeError("Script validation failed after max retries.")

    clip_paths = generate_all_clips(script=script, run_dir=run_dir, cfg=cfg)
    manifest["steps"]["generate"] = "completed"
    update_manifest(run_dir, manifest)

    normalized_paths = normalize_clips(clip_paths, run_dir=run_dir, cfg=cfg)
    final_video = assemble_video(normalized_paths, run_dir=run_dir, cfg=cfg)
    manifest["steps"]["assemble"] = "completed"
    update_manifest(run_dir, manifest)

    write_report(
        run_dir=run_dir,
        status="success",
        final_video=str(final_video),
        warnings=manifest["warnings"],
        validation=validation,
    )
    manifest["steps"]["report"] = "completed"
    manifest["status"] = "success"
    manifest["completed_at_utc"] = datetime.now(UTC).isoformat()
    update_manifest(run_dir, manifest)
    return final_video
