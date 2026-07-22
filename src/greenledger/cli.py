from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import run_pipeline

UTILITY_LABELS = {
    "electricity": "Electricity",
    "natural_gas": "Natural Gas",
    "water": "Water",
}


def _print_report(report, folder: Path) -> None:
    print(f"GreenLedger report for: {folder}")
    print("=" * 60)

    if report.errors:
        print("Skipped / unparsable files:")
        for err in report.errors:
            print(f"  - {err}")
        print()

    if not report.bills:
        print("No bills parsed. Nothing to report.")
        return

    print(f"Parsed {len(report.bills)} bill(s) across "
          f"{len({b.utility_type for b in report.bills})} utility type(s).\n")

    print("Trend:")
    for tp in report.trend_points:
        label = UTILITY_LABELS.get(tp.utility_type, tp.utility_type)
        pct = f"{tp.pct_vs_rolling_avg:+.0f}% vs 6-mo avg" if tp.pct_vs_rolling_avg is not None else "baseline"
        print(
            f"  [{label:11s}] {tp.period_start:%Y-%m} usage={tp.usage:>9.1f}  "
            f"co2e={tp.kg_co2e:>8.1f} kg  ({pct})"
        )
    print()

    print(f"Total footprint across all bills: {report.total_kg_co2e:.1f} kg CO2e\n")

    if report.recommendations:
        print("Recommendations (priority order):")
        for i, rec in enumerate(report.recommendations, start=1):
            print(f"  {i}. {rec.title}")
            print(f"     {rec.detail}")
    else:
        print("No usage spikes detected - no action items this period.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="greenledger",
        description="Estimate household carbon footprint from a folder of utility bills (fully offline).",
    )
    parser.add_argument("bills_folder", type=Path, help="Folder containing bill PDFs/images")
    args = parser.parse_args(argv)

    if not args.bills_folder.is_dir():
        print(f"Error: {args.bills_folder} is not a directory", file=sys.stderr)
        return 1

    report = run_pipeline(args.bills_folder)
    _print_report(report, args.bills_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
