#!/usr/bin/env python3
"""
Post-clone sanity check: Python version, optional .env, imports, MySQL connectivity.

Run from project root:
  python scripts/check_setup.py
  python scripts/check_setup.py --mysql
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify NetShield AI dev environment.")
    parser.add_argument(
        "--mysql",
        action="store_true",
        help="Try connecting to MySQL using app/common/db.py (requires .env).",
    )
    args = parser.parse_args()
    root = _root()
    errors = 0

    print(f"Project root: {root}")

    if sys.version_info < (3, 10):
        print("FAIL: Python 3.10+ required.", file=sys.stderr)
        errors += 1
    else:
        print(f"OK: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    env_path = root / ".env"
    example = root / ".env.example"
    if not env_path.is_file():
        print(f"WARN: Missing {env_path.name} — copy {example.name} and fill MySQL credentials.")
    else:
        print(f"OK: Found {env_path.name}")

    required_modules = [
        "torch",
        "streamlit",
        "pandas",
        "sqlalchemy",
        "pymysql",
        "scapy",
        "plotly",
        "requests",
        "cryptography",
    ]
    for name in required_modules:
        if importlib.util.find_spec(name) is None:
            print(f"FAIL: Python package not installed: {name} (pip install -r requirements.txt)", file=sys.stderr)
            errors += 1
        else:
            print(f"OK: import {name}")

    model = root / "edge_bert_quantized.pt"
    if not model.is_file():
        print(
            "WARN: edge_bert_quantized.pt not found — run run_training.py after adding data/*.csv "
            "or copy the bundle from another machine."
        )
    else:
        print(f"OK: Found {model.name}")

    data_csv = list((root / "data").glob("*.csv")) if (root / "data").is_dir() else []
    if not data_csv:
        print("WARN: No data/*.csv — training will fail until you add CICIDS-style CSVs.")
    else:
        print(f"OK: {len(data_csv)} CSV file(s) under data/")

    if args.mysql:
        try:
            sys.path.insert(0, str(root))
            from sqlalchemy import text

            from backend.common.db import get_db_session

            with get_db_session() as session:
                session.execute(text("SELECT 1"))
            print("OK: MySQL connection (SELECT 1)")
        except Exception as exc:
            print(f"FAIL: MySQL check: {exc}", file=sys.stderr)
            errors += 1

    if errors:
        print(f"\nDone with {errors} error(s).", file=sys.stderr)
        return 1
    print("\nAll automated checks passed (review WARN lines above).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
