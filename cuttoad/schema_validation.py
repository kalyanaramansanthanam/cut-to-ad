from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate

SCHEMA_DIR = Path(__file__).parent / "schemas"


def validate_artifact(schema_name: str, data: dict[str, Any]) -> None:
    schema_path = SCHEMA_DIR / schema_name
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    validate(instance=data, schema=schema)
