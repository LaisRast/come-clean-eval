from __future__ import annotations

import argparse
import subprocess
import sys

from models import REGISTRY


def main() -> None:
    parser = argparse.ArgumentParser(description="Run come-clean evals across the model registry")
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()

    models = ",".join(model.id for model in REGISTRY)
    result = subprocess.run(
        [
            "uv",
            "run",
            "inspect",
            "eval",
            "src/comeclean/task.py",
            "--model",
            models,
            "--epochs",
            str(args.epochs),
            "--timeout",
            "60",
            "--max-retries",
            "2",
        ]
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
