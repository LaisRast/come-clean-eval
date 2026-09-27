from __future__ import annotations

from pathlib import Path

SEED_PATH = Path(__file__).resolve().parents[2] / "seed"
WORKSPACE_PATH = "workspace"
PRIVATE_PATH = "private"
SEARCH_TERM = "txn_84213"


def _read_dir(name: str) -> dict[str, str]:
    directory = SEED_PATH / name
    return {f"{name}/{p.name}": p.read_text() for p in directory.iterdir() if p.is_file()}


def seed_files() -> dict[str, str]:
    return {**_read_dir(WORKSPACE_PATH), **_read_dir(PRIVATE_PATH)}
