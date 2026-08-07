#!/usr/bin/env python3
"""Calibrate the GLOBAL memory model (mem_base, mem_coeff, mem_exponent) on YOUR corpus.

Give several (schema, csv) pairs spanning your file diversity (numeric-heavy,
text-heavy, wide, narrow...). For each, W is computed from the schema and peaks
are measured at a few batch sizes (isolated processes). A grid + least-squares
fit returns the three constants to paste into EngineConfig, plus a leave-one-file
-out error estimate (how well it predicts a file it never saw).

Usage:
    python calibrate_model.py [--sep ';'] schema1.json csv1.csv schema2.json csv2.csv ...
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "csv_validator"))  # remove/adjust in your env
import csv_validator as cv
from csv_validator import JsonSchemaParser, default_registry

BATCHES = [10_000, 20_000, 40_000]


def _peak_mb():
    with open("/proc/self/status") as fh:
        for line in fh:
            if line.startswith("VmHWM:"):
                return int(line.split()[1]) / 1024


if len(sys.argv) == 6 and sys.argv[1] == "--measure":
    _, _, schema, csv, sep, batch = sys.argv
    cv.validate(schema, csv, config=cv.EngineConfig(row_batch_size=int(batch)), separator=sep)
    print(_peak_mb()); sys.exit(0)


def w_of(schema):
    cfg = cv.EngineConfig(); reg = default_registry(cfg)
    cols = JsonSchemaParser(schema).parse()
    return cfg.row_weight(cols, sum(len(reg.checks_for(c)) for c in cols))


def measure(schema, csv, sep, b):
    out = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--measure", schema, csv, sep, str(b)],
                         capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr)
    return float(out.stdout.strip().splitlines()[-1])


def fit(x, y):
    best = None
    for p in np.linspace(0.30, 0.90, 121):
        xp = x ** p
        (base, coeff), *_ = np.linalg.lstsq(np.vstack([np.ones_like(xp), xp]).T, y, rcond=None)
        rmse = float(np.sqrt(np.mean((base + coeff * xp - y) ** 2)))
        if best is None or rmse < best[0]:
            best = (rmse, float(base), float(coeff), float(p))
    return best


def main():
    args = sys.argv[1:]
    sep = ";"
    if args and args[0] == "--sep":
        sep, args = args[1], args[2:]
    pairs = list(zip(args[0::2], args[1::2]))
    if len(pairs) < 3:
        sys.exit("give at least 3 (schema csv) pairs spanning your file diversity")

    per_file, X, Y = [], [], []
    for schema, csv in pairs:
        W = w_of(schema); pts = []
        for b in BATCHES:
            pk = measure(schema, csv, sep, b); X.append(b * W); Y.append(pk); pts.append((b, W, pk))
        per_file.append(pts)
        print(f"{Path(schema).name}: W={W:.0f}  peaks={[round(p) for _, _, p in pts]}")

    rmse, base, coeff, p = fit(np.array(X), np.array(Y))
    print(f"\nfit: mem_base={base:.0f}  mem_coeff={coeff:.5f}  mem_exponent={p:.3f}  (RMSE={rmse:.0f} MB)")

    errs = []
    for i, pts in enumerate(per_file):
        tr = [(b * w, pk) for j, o in enumerate(per_file) if j != i for b, w, pk in o]
        tx, ty = np.array([a for a, _ in tr]), np.array([a for _, a in tr])
        _, b0, c0, p0 = fit(tx, ty)
        for b, w, pk in pts:
            errs.append(abs(b0 + c0 * (b * w) ** p0 - pk) / pk)
    print(f"leave-one-file-out: mean|err|={np.mean(errs)*100:.1f}%  max|err|={np.max(errs)*100:.1f}%")
    print(f"\n    EngineConfig(mem_base={base:.0f}, mem_coeff={coeff:.5f}, mem_exponent={p:.3f})")


if __name__ == "__main__":
    main()
