from __future__ import annotations

import os
from pathlib import Path

import click
from loguru import logger

from cuttoad.config import Config, load_config
from cuttoad.io_utils import read_json
from cuttoad.pipeline import run_pipeline
from cuttoad.schema_validation import validate_artifact


def run_doctor(cfg: Config) -> int:
    checks: list[tuple[str, bool, str]] = [
        ("ffmpeg", cfg.ffmpeg_path is not None, cfg.ffmpeg_path or "not found"),
        ("ffprobe", cfg.ffprobe_path is not None, cfg.ffprobe_path or "not found"),
        (
            "output_dir_writable",
            _is_writable_dir(cfg.output_root),
            str(cfg.output_root),
        ),
        (
            "google_api_key",
            bool(cfg.google_api_key),
            "present" if cfg.google_api_key else "missing (provider integration pending)",
        ),
        (
            "minimax_api_key",
            bool(cfg.minimax_api_key),
            "present" if cfg.minimax_api_key else "missing (provider integration pending)",
        ),
        (
            "aws_access_key_id",
            bool(os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE")),
            "present" if os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE") else "missing",
        ),
    ]

    has_failures = False
    for name, passed, details in checks:
        marker = "OK" if passed else "WARN"
        level = "INFO"
        if name in {"ffmpeg", "ffprobe", "output_dir_writable"} and not passed:
            marker = "FAIL"
            level = "ERROR"
            has_failures = True
        elif not passed:
            level = "WARNING"
        logger.log(level, f"[{marker}] {name}: {details}")
    return 1 if has_failures else 0


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".cuttoad_write_check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def validate_run(cfg: Config, run_id: str) -> int:
    run_dir = cfg.output_root / run_id
    required = [
        run_dir / "manifest.json",
        run_dir / "analysis.v1.json",
        run_dir / "script.v1.json",
        run_dir / "validation.v1.json",
        run_dir / "report.v1.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        logger.error("Missing artifacts:")
        for path in missing:
            logger.error(f"- {path}")
        return 1

    validators = [
        ("manifest.v1.schema.json", run_dir / "manifest.json"),
        ("analysis.v1.schema.json", run_dir / "analysis.v1.json"),
        ("script.v1.schema.json", run_dir / "script.v1.json"),
        ("validation.v1.schema.json", run_dir / "validation.v1.json"),
        ("report.v1.schema.json", run_dir / "report.v1.json"),
    ]
    for schema_name, artifact_path in validators:
        payload = read_json(artifact_path)
        validate_artifact(schema_name, payload)
    logger.info(f"Run artifacts validated: {run_dir}")
    return 0


@click.group()
def main() -> None:
    """CutToad CLI."""


@main.command(name="doctor")
def doctor_cmd() -> None:
    """Validate runtime dependencies and environment."""
    cfg = load_config()
    code = run_doctor(cfg)
    if code != 0:
        raise click.exceptions.Exit(code)


@main.command(name="validate-run")
@click.argument("run_id")
def validate_run_cmd(run_id: str) -> None:
    """Validate artifacts for a run id."""
    cfg = load_config()
    code = validate_run(cfg, run_id)
    if code != 0:
        raise click.exceptions.Exit(code)


@main.command(name="run")
@click.argument("video", type=click.Path(exists=True, path_type=Path))
@click.option("--product", required=True, help="Product/brand brief text.")
@click.option("--audience", required=True, help="Audience persona text.")
@click.option("--run-id", default=None, help="Optional explicit run id.")
@click.option(
    "--max-scenes",
    type=click.IntRange(min=1),
    default=None,
    help="Scene count (default from config, must be >= 1).",
)
def run_cmd(video: Path, product: str, audience: str, run_id: str | None, max_scenes: int | None) -> None:
    """Execute a CutToad pipeline run."""
    cfg = load_config()
    resolved_max_scenes = max_scenes or cfg.default_scenes
    if resolved_max_scenes < 1:
        raise click.BadParameter("must be >= 1", param_hint="--max-scenes")
    final_video = run_pipeline(
        cfg=cfg,
        video_path=video.resolve(),
        product=product,
        audience=audience,
        run_id=run_id,
        max_scenes=resolved_max_scenes,
    )
    logger.info(f"Run complete. Output: {final_video}")


if __name__ == "__main__":
    main()
