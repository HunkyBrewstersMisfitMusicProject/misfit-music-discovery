#!/usr/bin/env python3
"""Validate every artist manifest against manifest.schema.json.

Usage:
    python3 validate_manifests.py

Exits non-zero if any manifest fails validation. Safe to wire into CI.
Requires no third-party packages: uses jsonschema if available, otherwise a
built-in fallback that checks the structural essentials.
"""
import json
import glob
import sys
import os

SCHEMA = "manifest.schema.json"
ROOT = os.path.dirname(os.path.abspath(__file__))


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    schema_path = os.path.join(ROOT, SCHEMA)
    manifests = sorted(
        f for f in glob.glob(os.path.join(ROOT, "*.json"))
        if os.path.basename(f) not in ("registry.json", "curators.json", SCHEMA)
    )

    try:
        import jsonschema  # type: ignore
        from jsonschema import Draft202012Validator
        schema = load(schema_path)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        use_jsonschema = True
    except ImportError:
        use_jsonschema = False

    errors = 0
    for path in manifests:
        name = os.path.basename(path)
        data = load(path)
        if use_jsonschema:
            errs = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errs:
                errors += 1
                print(f"FAIL {name}")
                for e in errs:
                    loc = "/".join(str(p) for p in e.path) or "<root>"
                    print(f"    - {loc}: {e.message}")
            else:
                print(f"ok   {name}")
        else:
            # Fallback: enforce the essentials without jsonschema installed.
            required = ["manifest_version", "generated_at", "name",
                        "location", "genres", "bio", "links"]
            ok = True
            for r in required:
                if r not in data:
                    print(f"FAIL {name}: missing required '{r}'"); ok = False
            if not isinstance(data.get("genres"), list) or not data["genres"]:
                print(f"FAIL {name}: 'genres' must be a non-empty list"); ok = False
            if not isinstance(data.get("links"), list):
                print(f"FAIL {name}: 'links' must be a list"); ok = False
            if "preview" in data and not (data["preview"] is None or isinstance(data["preview"], str)):
                print(f"FAIL {name}: 'preview' must be string or null"); ok = False
            if ok:
                print(f"ok   {name}")
            else:
                errors += 1

    if errors:
        print(f"\n{errors} manifest(s) failed validation.")
        sys.exit(1)
    print(f"\nAll {len(manifests)} manifests valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
