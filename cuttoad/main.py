from __future__ import annotations

import argparse
import os
from pathlib import Path

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
        if name in {"ffmpeg", "ffprobe", "output_dir_writable"} and not passed:
            marker = "FAIL"
            has_failures = True
        print(f"[{marker}] {name}: {details}")
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
        print("Missing artifacts:")
        for path in missing:
            print(f"- {path}")
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
    print(f"Run artifacts validated: {run_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    def positive_int(value: str) -> int:
        parsed = int(value)
        if parsed < 1:
            raise argparse.ArgumentTypeError("must be >= 1")
        return parsed

    parser = argparse.ArgumentParser(prog="cuttoad")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Validate runtime dependencies and environment.")

    run_parser = subparsers.add_parser("run", help="Execute a CutToad pipeline run.")
    run_parser.add_argument("video", help="Path to input video file.")
    run_parser.add_argument("--product", required=True, help="Product/brand brief text.")
    run_parser.add_argument("--audience", required=True, help="Audience persona text.")
    run_parser.add_argument("--run-id", default=None, help="Optional explicit run id.")
    run_parser.add_argument(
        "--max-scenes",
        type=positive_int,
        default=None,
        help="Scene count (default from config, must be >= 1).",
    )

    validate_parser = subparsers.add_parser("validate-run", help="Validate artifacts for a run id.")
    validate_parser.add_argument("run_id", help="Run identifier, e.g., run_20260221T... ")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cfg = load_config()

    if args.command == "doctor":
        raise SystemExit(run_doctor(cfg))

    if args.command == "validate-run":
        raise SystemExit(validate_run(cfg, args.run_id))

    if args.command == "run":
        video_path = Path(args.video).resolve()
        max_scenes = args.max_scenes or cfg.default_scenes
        if max_scenes < 1:
            raise SystemExit("Invalid scene count: must be >= 1")
        final_video = run_pipeline(
            cfg=cfg,
            video_path=video_path,
            product=args.product,
            audience=args.audience,
            run_id=args.run_id,
            max_scenes=max_scenes,
        )
        print(f"Run complete. Output: {final_video}")
        raise SystemExit(0)

    parser.print_help()
    raise SystemExit(2)


if __name__ == "__main__":
    main()
