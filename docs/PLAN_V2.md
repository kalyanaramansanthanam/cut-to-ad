# CutToad Plan v2

## Goal
- Input: `source_video.mp4`, `product_brief` text, `audience_persona` text.
- Output: a ~20-second personalized product-placement ad video.

## Architecture
- Reproducible orchestration pipeline (not deterministic generation).
- Steps:
1. Analyze source video.
2. Generate script (4 scenes by default).
3. Validate script (rule-based + model-based).
4. Generate clips in parallel.
5. Normalize media and assemble final video.
6. Run final quality gate and write run report.

## Non-Negotiables
- Every step writes versioned JSON artifacts.
- Each run has a unique `run_id` and manifest.
- Resume from checkpoints is supported.
- All network/model calls have timeout, retry, and budget controls.
- Safety checks run before clip generation.

## Artifacts
- Output path: `output/<run_id>/`.
- Required files:
  - `manifest.json`
  - `analysis.v1.json`
  - `script.v1.json`
  - `validation.v1.json`
  - `clips/clip_01.mp4` .. `clips/clip_04.mp4`
  - `assemble_plan.v1.json`
  - `final_ad.mp4`
  - `report.v1.json`

## Pipeline Steps and Acceptance Criteria

### 1) Setup and Preflight
- Validate required env vars and binaries.
- Validate provider/model config at startup.
- Acceptance: `cuttoad doctor` fails fast with actionable error messages.

### 2) Analyze Video
- Extract scene-by-scene and style metadata from source video.
- Acceptance: analysis artifact validates schema and includes required fields:
  - `scenes[]`, `timestamps`, `visual_style`, `pacing`, `lighting`, `mood`.

### 3) Generate Script
- Produce exactly N scenes (default 4) with per-scene duration targets.
- Include product integration and audience personalization requirements.
- Acceptance: script artifact is schema-valid and total duration is 18-24 seconds.

### 4) Validate Script
- Layer A: deterministic checks (schema, duration, CTA presence, disallowed terms).
- Layer B: model-based scoring (`style`, `product`, `audience`, `flow`).
- Max 3 script revisions.
- Acceptance: both validation layers pass, or run stops with explicit reasons.

### 5) Generate Clips (Parallel)
- Submit generation jobs concurrently with bounded worker count.
- Poll with exponential backoff + jitter.
- Acceptance: each scene ends in explicit state: `success` or `failed`.

### 6) Degraded-Mode Rules
- If one scene fails: regenerate once using simplified prompt.
- If still failing: insert fallback scene asset.
- If more than one scene fails: fail run unless `--allow-degraded`.
- Acceptance: pipeline exits with explicit final status and rationale.

### 7) Normalize and Assemble
- Normalize all clips to uniform codec/fps/resolution/audio.
- Assemble final output with reliable concat path.
- Acceptance: output passes playback check and ffprobe stream consistency checks.

### 8) Final Quality Gate
- Confirm expected duration, scene order, and CTA presence.
- Write summary report with quality scores, warnings, and failure notes.
- Acceptance: `report.v1.json` present and machine-readable.

## Runtime Controls
- Per-step timeout and retry policy.
- Global run timeout via `--max-minutes`.
- Budget cap via `--budget-usd`.
- Concurrency cap for clip generation workers.

## CLI Contract
- `cuttoad run <video> --product "<text>" --audience "<text>"`
- Optional flags:
  - `--run-id`
  - `--resume`
  - `--max-scenes`
  - `--allow-degraded`
  - `--budget-usd`
  - `--max-minutes`
- Utility commands:
  - `cuttoad doctor`
  - `cuttoad validate-run <run_id>`

## Suggested File Layout
- `cuttoad/main.py` (CLI + orchestration)
- `cuttoad/config.py` (env/config + preflight)
- `cuttoad/schemas/*.json` (artifact schemas)
- `cuttoad/tools/analyze_video.py`
- `cuttoad/agents/scriptwriter.py`
- `cuttoad/agents/validator.py`
- `cuttoad/tools/generate_clips.py`
- `cuttoad/tools/normalize_media.py`
- `cuttoad/tools/assemble_video.py`
- `cuttoad/tools/reporting.py`

## Test Plan
1. Schema validation tests for every artifact.
2. Provider contract tests with mocked responses.
3. Retry/backoff tests with injected transient failures.
4. Resume tests from each checkpoint.
5. Media assembly tests with intentionally mismatched clip properties.
6. E2E happy path test and degraded path test.

## Risks and Mitigations
- Provider API drift: capability preflight + contract tests.
- Rate limits: bounded concurrency + retry/backoff + queueing.
- Safety/compliance: pre-generation moderation and audit trail in report.
- Cost overrun: hard budget cap and early stop behavior.

## Definition of Done
- Single command produces either:
  - `final_ad.mp4`, or
  - explicit failed status with diagnostics.
- Resume works from interrupted run.
- Degraded behavior is documented and predictable.
- Final report includes runtime, quality summary, and failure metadata.
