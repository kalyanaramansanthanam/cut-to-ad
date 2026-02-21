# CutToad

Implementation plan lives in `docs/PLAN_V2.md`.

## Current Status

Initial implementation scaffolding is in place:
- CLI commands: `cuttoad doctor`, `cuttoad run`, `cuttoad validate-run`
- Checkpointed artifacts under `output/<run_id>/`
- JSON schema validation for manifest and core artifacts
- Stub generation path for clip creation using ffmpeg

## Quick Start

```bash
uv sync
uv run cuttoad doctor
uv run cuttoad run ./path/to/input.mp4 --product "Brand X hydration mix" --audience "college athletes"
```
