from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from models import REGISTRY


def load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def fetch_models(api_key: str) -> list[dict]:
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["data"]


def is_thinking(model_data: dict) -> bool:
    params = model_data.get("supported_parameters") or []
    return any(p in ("reasoning", "thinking", "include_reasoning") for p in params)


def format_date(ts: int | None) -> str:
    if ts is None:
        return "unknown"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def main() -> None:
    api_key = load_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print("Fetching models from OpenRouter...", flush=True)
    api_data = fetch_models(api_key)
    by_id = {m["id"]: m for m in api_data}

    # (api_display_name, id, provider, thinking, created, flag)
    rows = []
    issues = []
    for model in REGISTRY:
        api_id = model.id.removeprefix("openrouter/")
        api_model = by_id.get(api_id)
        if api_model is None:
            rows.append((model.display_name, api_id, model.vendor, "?", "?", "NOT FOUND"))
            issues.append(f"  NOT FOUND  {model.id}")
            continue
        api_name = api_model.get("name", "")
        # OpenRouter prefixes every name with "Provider: "; strip it.
        api_name_bare = api_name.split(": ", 1)[-1]
        name_match = model.display_name == api_name_bare
        api_created = format_date(api_model.get("created"))
        created_match = model.created == api_created
        flags = []
        if not name_match:
            flags.append("NAME DIFF")
        if not created_match:
            flags.append("CREATED DIFF")
        rows.append((
            api_name_bare,
            api_id,
            model.vendor,
            "yes" if is_thinking(api_model) else "no",
            api_created,
            ", ".join(flags),
        ))
        if not name_match:
            issues.append(f"  NAME DIFF  {model.id}\n    ours: {model.display_name}\n    api:  {api_name_bare}")
        if not created_match:
            issues.append(f"  CREATED DIFF  {model.id}\n    ours: {model.created}\n    api:  {api_created}")

    if not rows:
        print("REGISTRY is empty: nothing to check.")
        return

    headers = ("Display Name", "ID", "Vendor", "Thinking", "Created", "")
    col_widths = [max(len(r[i]) for r in rows) for i in range(6)]
    col_widths = [max(col_widths[i], len(headers[i])) for i in range(6)]

    sep = "  ".join("-" * w for w in col_widths)
    print()
    print("  ".join(h.ljust(w) for h, w in zip(headers, col_widths)))
    print(sep)
    for row in rows:
        print("  ".join(v.ljust(w) for v, w in zip(row, col_widths)))

    if issues:
        print(f"\n{len(issues)} issue(s) found:")
        for msg in issues:
            print(msg)
    else:
        print("\nAll models found, names and created dates match.")


if __name__ == "__main__":
    main()
