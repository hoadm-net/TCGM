"""Run the LongMemEval-V2 adapter and emit canonical Parquet artifacts.

Usage:
    python scripts/run_adapter_lmev2.py [--haystack small|medium|both]

Outputs written to:  artifacts/adapters/longmemeval_v2/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from project root without installing the package
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tcgm.adapters.longmemeval_v2 import LongMemEvalV2Adapter


DATA_ROOT = ROOT / "datasets" / "LongMemEval-V2" / "data" / "longmemeval-v2"
OUTPUT_DIR = ROOT / "artifacts" / "adapters" / "longmemeval_v2"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build TCGM graph from LongMemEval-V2")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DATA_ROOT,
        help="Path to the longmemeval-v2 data directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Where to write Parquet files and validation.json",
    )
    args = parser.parse_args()

    print(f"Data root : {args.data_root}")
    print(f"Output dir: {args.output_dir}")
    print()

    adapter = LongMemEvalV2Adapter(
        data_root=args.data_root,
        output_dir=args.output_dir,
    )
    paths, report = adapter.run()

    print("\n=== Output files ===")
    for name, p in paths.items():
        size_kb = p.stat().st_size // 1024
        print(f"  {name:15s}: {p}  ({size_kb} KB)")

    print("\n=== Validation report ===")
    print(json.dumps(report, indent=2))

    if not report["ok"]:
        print("\n[FAIL] Validation errors found — see report above.")
        sys.exit(1)
    else:
        print("\n[OK] All validation checks passed.")


if __name__ == "__main__":
    main()
