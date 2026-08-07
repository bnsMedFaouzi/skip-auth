#!/usr/bin/env python3
"""Calibrate the memory model on a REAL file: find bytes_per_cell and baseline_mb.

Model:  peak_mb  ~=  baseline_mb  +  bytes_per_cell * rows_in_flight * series
        series   =   columns + total checks (read from the schema + registry)

Runs several forced batch sizes, each in a FRESH process (clean peak on every OS,
macOS included), then least-squares-fits a line through (rows*series, peak).
Slope = bytes_per_cell, intercept = baseline_mb.

Usage:  python calibrate.py <schema.json> <data.csv> <separator>
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "csv_validator"))
warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve()
BATCHES = [10_000, 20_000, 40_000, 80_000, 160_000]


def _peak_mb() -> float:
    with open("/proc/self/status") as fh:
        for line in fh:
            if line.startswith("VmHWM:"):
                return int(line.split()[1]) / 1024
    return 0.0


if len(sys.argv) == 6 and sys.argv[1] == "--measure":
    import csv_validator as cv
    _, _, schema, csv, sep, batch = sys.argv
    cfg = cv.EngineConfig(row_batch_size=int(batch))
    report = cv.validate(schema, csv, config=cfg, separator=sep)
    print(json.dumps({"batch": int(batch), "rows": report.file.rows, "peak_mb": _peak_mb()}))
    sys.exit(0)


def _measure(schema, csv, sep, batch):
    out = subprocess.run([sys.executable, str(HERE), "--measure", schema, csv, sep, str(batch)],
                         capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr)
    return json.loads(out.stdout.strip().splitlines()[-1])


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: python calibrate.py <schema.json> <data.csv> <separator>")
    schema, csv, sep = sys.argv[1], sys.argv[2], sys.argv[3]

    import csv_validator as cv
    from csv_validator import JsonSchemaParser, default_registry
    reg = default_registry(cv.EngineConfig())
    columns = JsonSchemaParser(schema).parse()
    series = len(columns) + sum(len(reg.checks_for(c)) for c in columns)
    print(f"schema: {len(columns)} columns + {series - len(columns)} checks = {series} series\n")

    pts = []
    for b in BATCHES:
        r = _measure(schema, csv, sep, b)
        if r["rows"] < b:
            print(f"  batch {b:>8,}  (file has only {r['rows']:,} rows -- skipped)")
            continue
        pts.append((b * series, r["peak_mb"]))
        print(f"  batch {b:>8,}  peak {r['peak_mb']:6.0f} MB")

    if len(pts) < 2:
        sys.exit("\nNeed at least two batch sizes below the row count to calibrate.")

    n = len(pts)
    sx = sum(x for x, _ in pts); sy = sum(y for _, y in pts)
    sxx = sum(x * x for x, _ in pts); sxy = sum(x * y for x, y in pts)
    m = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    a = (sy - m * sx) / n
    print(f"\nfit: bytes_per_cell = {m * 1e6:.1f}   baseline_mb = {a:.0f}")
    print(f"\n    EngineConfig(bytes_per_cell={m * 1e6:.0f}, baseline_mb={max(a, 0):.0f})")


if __name__ == "__main__":
    main()
