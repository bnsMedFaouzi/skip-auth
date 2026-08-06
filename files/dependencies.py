"""Benchmark the CSV validator on YOUR files (a JSON schema + a CSV).

Usage
-----
Edit the constants at the top of `main()` (SCHEMA, CSV, ISOLATED), then just run
this file (e.g. the Run button in your IDE). No command-line needed. Everything
else (date format, streaming, batch) uses EngineConfig defaults — change them in
EngineConfig if yours differ.

Set ISOLATED = True to run each measurement in its own process: peaks are then
clean on every OS (including macOS), at the cost of a fresh interpreter per case.
With ISOLATED = False (default) cases share one process; peaks rely on the
clear_refs reset, which works on Linux but not macOS.

Method
------
Each case runs in-process. Peak memory is read from `/proc/self/status` (VmHWM)
on Linux, `ru_maxrss` elsewhere. Because that peak is a per-process high-water
mark that never decreases, we reset it before each case (Linux, best-effort) so
every measurement reports its own peak rather than the running maximum.

What it reports
---------------
1. Headline   -> time, throughput, peak memory, rows, errors
2. Batch size -> row_batch_size is a memory knob, not a speed knob
3. Engine     -> streaming vs in-memory

Notes
-----
- suite(..., quick=True) runs the headline only (handy on very large files).
- Set EngineConfig.default_date_format to match your Date columns.
- Throughput is per available core; check the printed core count.
- Peak reset relies on /proc (Linux); on macOS peaks across cases stay monotone.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                       # dir containing the `csv_validator` package


# --------------------------------------------------------------------------- #
# One measurement (runs in-process; peak counter reset before each)
# --------------------------------------------------------------------------- #

def _reset_peak_rss() -> None:
    """Reset the kernel peak-RSS counter (Linux 4.0+) so the next measurement
    reports its own peak, not the running maximum. Best-effort: no-op elsewhere."""
    try:
        with open("/proc/self/clear_refs", "w", encoding="ascii") as fh:
            fh.write("5")
    except OSError:
        pass


def _peak_rss_mb() -> float:
    """Peak resident-set size in MB.

    On Linux we read `/proc/self/status` VmHWM, which prints its unit explicitly
    (e.g. "kB") — the kernel tells us the unit, so nothing is assumed. Elsewhere
    (macOS/BSD, no /proc) we fall back to `ru_maxrss`, whose unit POSIX leaves to
    the OS: bytes on macOS/BSD, kilobytes on other Unix.
    """
    try:
        with open("/proc/self/status", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("VmHWM:"):
                    _, value, unit = line.split()
                    factor = {"B": 1 / 1024 / 1024, "kB": 1 / 1024, "mB": 1.0}
                    return int(value) * factor.get(unit, 1 / 1024)
    except OSError:
        pass  # no /proc (macOS/BSD): fall back to ru_maxrss below

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin" or "bsd" in sys.platform:
        return rss / 1024 / 1024          # bytes -> MB
    return rss / 1024                     # kilobytes -> MB


def measure(schema: str, csv: str, streaming: bool, batch: int) -> dict:
    """Run one validation in-process and return its timing/memory/result metrics.

    Everything except the axis under test (streaming / batch) uses EngineConfig
    defaults — notably the date format (set it in EngineConfig if yours differs).
    """
    warnings.filterwarnings("ignore")
    sys.path.insert(0, str(ROOT))
    import csv_validator as cv

    row_batch_size = None if batch <= 0 else batch   # <=0 -> auto-size from column count
    cfg = cv.EngineConfig(streaming=streaming, row_batch_size=row_batch_size)
    _reset_peak_rss()
    start = time.perf_counter()
    report = cv.validate(schema, csv, config=cfg)
    elapsed = time.perf_counter() - start
    return {
        "time": elapsed, "peak_mb": _peak_rss_mb(),
        "rows": report.file.rows, "cols": report.file.columns_present,
        "errors": report.file.total_errors, "status": report.status,
    }


def run_case(schema: Path, csv: Path, *, streaming: bool, batch: int, isolated: bool = False) -> dict:
    """Run one measurement and return its result.

    isolated=False -> in-process (fast). isolated=True -> a fresh process, for a
    clean, uncontaminated peak on every OS (no reliance on the clear_refs reset).
    """
    if isolated:
        return _measure_in_subprocess(schema, csv, streaming=streaming, batch=batch)
    return measure(str(schema), str(csv), streaming, batch)


def _measure_in_subprocess(schema: Path, csv: Path, *, streaming: bool, batch: int) -> dict:
    """Run one measurement in a fresh process and return its parsed result."""
    proc = subprocess.run(
        [sys.executable, str(HERE / "run_bench.py"), "--measure",
         str(schema), str(csv), str(streaming), str(batch)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"measurement failed:\n{proc.stderr}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def suite(schema: Path, csv: Path, quick: bool = False, isolated: bool = False) -> None:
    if not schema.exists():
        sys.exit(f"schema not found: {schema}")
    if not csv.exists():
        sys.exit(f"csv not found: {csv}")

    size_mb = csv.stat().st_size / 1e6
    ncpu = os.cpu_count() or 1
    mode = "isolated processes" if isolated else "in-process"
    print(f"file: {csv.name}  ({size_mb:.0f} MB)   schema: {schema.name}   cores: {ncpu}   [{mode}]")
    print()

    # 1) headline (streaming, auto batch = the real default)
    print("== 1. headline (streaming, auto batch) ==")
    r = run_case(schema, csv, streaming=True, batch=0, isolated=isolated)
    print(f"  status   : {r['status']}")
    print(f"  rows     : {r['rows']:,}")
    print(f"  errors   : {r['errors']:,}")
    print(f"  time     : {r['time'] * 1000:.1f} ms   ({size_mb / r['time']:.1f} MB/s on {ncpu} core(s))")
    print(f"  peak mem : {r['peak_mb']:.0f} MB")
    import csv_validator as cv
    est = cv.EngineConfig().estimated_peak_mb(r["cols"])
    print(f"  model est: {est:.0f} MB   (auto batch, {r['cols']} cols — recalibrate if far)")

    if quick:
        return

    # 2) batch-size sweep -> memory knob, not speed knob
    print("\n== 2. batch size (memory vs speed) ==")
    print(f"{'batch':>8} | {'time ms':>8} | {'peak MB':>8}")
    for batch in (20_000, 50_000, 100_000, 200_000):
        r = run_case(schema, csv, streaming=True, batch=batch, isolated=isolated)
        print(f"{batch:>8} | {r['time'] * 1000:8.1f} | {r['peak_mb']:8.0f}")

    # 3) streaming vs in-memory
    print("\n== 3. engine ==")
    print(f"{'engine':>10} | {'time ms':>8} | {'peak MB':>8}")
    for streaming in (True, False):
        r = run_case(schema, csv, streaming=streaming, batch=0, isolated=isolated)
        print(f"{'streaming' if streaming else 'in-memory':>10} | {r['time'] * 1000:8.1f} | {r['peak_mb']:8.0f}")


def main() -> None:
    # internal: an isolated child process measures one case and prints its JSON
    if len(sys.argv) == 6 and sys.argv[1] == "--measure":
        _, _, schema, csv, streaming, batch = sys.argv
        print(json.dumps(measure(schema, csv, streaming == "True", int(batch))))
        return

    # ---- edit these, then just run the file ------------------------------
    SCHEMA   = ROOT / "example" / "passive_sr_schema.json"   # path to the JSON schema
    CSV      = ROOT / "example" / "sample_data.csv"          # path to the CSV to validate
    ISOLATED = False                                         # True = one process per measurement
    # everything else uses EngineConfig defaults
    # ----------------------------------------------------------------------
    suite(Path(SCHEMA), Path(CSV), isolated=ISOLATED)


if __name__ == "__main__":
    main()
