"""PROTOTYPE — not wired into the package (no codebase changes).

Shows the three classes we discussed:

  MaskProcessor  (base)  — evaluate a set of named boolean masks over a block in a
                           single Polars collect, and accumulate per-mask a failing
                           count + a bounded sample (absolute line no. + value(s)).
  ColumnRunner   (sub)   — per-column checks; adds the per-column failing-row count
                           and regroups results under each column (today's behavior).
  RowRunner      (sub)   — cross-column integrity checks; sample shows the involved
                           columns; flat result list. Almost empty — the sign the
                           split is right.

Only `_build_sample_expr`, `_sample_payload` and `_assemble` vary between the two
subclasses; everything else lives once in the base. Both run as independent
`BlockProcessor`s (separate collect each) — the Runner already accepts a list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from csv_validator.models import BoundCheck          # existing: .column / .check / .invalid
from csv_validator.execution.runner import BlockProcessor

ROW_IDX = "__row__"  # transient per-block row index used to number samples


# --------------------------------------------------------------------------- #
# The cross-column rule object (mirrors BoundCheck; would live in validators/rows)
# --------------------------------------------------------------------------- #
@dataclass
class RowCheck:
    """A vectorized integrity rule over a whole row: name, involved columns, mask."""

    name: str
    columns: list[str]
    invalid: pl.Expr            # boolean expr combining several columns; True = violation


# Result shapes
CheckData = tuple[str, int, list[tuple[int, Any]]]     # (name, error_count, sample)
ColumnData = tuple[str, int, list[CheckData]]          # (column, failing_rows, checks)
RowData = CheckData                                    # (name, error_count, sample)


# --------------------------------------------------------------------------- #
# Base: one collect over a block -> counts + bounded samples per mask
# --------------------------------------------------------------------------- #
class MaskProcessor(BlockProcessor):
    """Evaluate named boolean masks over each block and accumulate their results.

    Knows nothing about "column" or "row": it works on any objects exposing an
    ``.invalid`` Polars expression. Per block it runs ONE streaming collect that
    computes, for every mask ``m{i}``: the failing count and a bounded sample.
    Subclasses decide only what a sample looks like and how to shape the result.
    """

    def __init__(self, checks: list[Any], sample_size: int, engine: str = "streaming") -> None:
        self._checks = list(checks)                       # each exposes `.invalid`
        self._sample_size = sample_size
        self._engine = engine
        # Data-independent expressions, built once and reused every block.
        self._masks = self._mask_exprs()
        self._rows_expr = pl.len().alias("rows")
        self._count_exprs = self._make_count_exprs()
        self._sample_exprs = self._make_sample_exprs()
        # Accumulators, parallel to `_checks`.
        self._counts = [0] * len(self._checks)
        self._samples: list[list[tuple[int, Any]]] = [[] for _ in self._checks]
        self._needs_sample = [sample_size > 0 for _ in self._checks]

    # -- BlockProcessor interface ------------------------------------------- #
    def update(self, block: pl.LazyFrame, offset: int) -> int:
        """Evaluate one block, fold it in, and return its row count.

        ``offset`` (rows seen before this block) makes sample line numbers absolute.
        """
        row = self._evaluate(block)
        self._accumulate(row, offset)
        return int(row["rows"])

    def result(self) -> Any:
        return self._assemble()

    # -- one Polars pass over one block ------------------------------------- #
    def _evaluate(self, block: pl.LazyFrame) -> dict:
        """Attach masks + aggregates to the lazy block, collect once, return one row."""
        return (
            block.with_row_index(ROW_IDX)
            .with_columns(self._masks)
            .select(self._aggregates())
            .collect(engine=self._engine)
            .row(0, named=True)
        )

    def _aggregates(self) -> list[pl.Expr]:
        """Row count, per-mask counts, and the samples still being collected."""
        samples = [self._sample_exprs[i] for i in range(len(self._checks)) if self._needs_sample[i]]
        return [self._rows_expr, *self._count_exprs, *samples]

    # -- expression builders (each list built once) ------------------------- #
    def _mask_exprs(self) -> list[pl.Expr]:
        """One invalid-mask ``m{i}`` per check (null cells are not invalid here)."""
        return [chk.invalid.fill_null(False).alias(f"m{i}") for i, chk in enumerate(self._checks)]

    def _make_count_exprs(self) -> list[pl.Expr]:
        """One failing-row count per mask (the sum of its mask)."""
        return [pl.col(f"m{i}").sum().alias(f"count:{i}") for i in range(len(self._checks))]

    def _make_sample_exprs(self) -> list[pl.Expr]:
        """One bounded sample per mask; the projection is subclass-specific."""
        return [
            self._build_sample_expr(i, chk)
            .filter(pl.col(f"m{i}"))
            .head(self._sample_size)
            .implode()
            .alias(f"sample:{i}")
            for i, chk in enumerate(self._checks)
        ]

    # -- accumulation across blocks ----------------------------------------- #
    def _accumulate(self, row: dict, offset: int) -> None:
        """Add one block's counts and samples to the totals."""
        for i in range(len(self._checks)):
            self._counts[i] += int(row[f"count:{i}"] or 0)
            if self._needs_sample[i]:
                self._collect_sample(i, row, offset)

    def _collect_sample(self, i: int, row: dict, offset: int) -> None:
        """Append mask ``i``'s sample rows (offset-shifted), stopping once it is full."""
        for rec in row[f"sample:{i}"] or []:
            if len(self._samples[i]) >= self._sample_size:
                self._needs_sample[i] = False
                return
            line = offset + int(rec["line"])
            self._samples[i].append((line, self._sample_payload(self._checks[i], rec)))

    # -- variation points (subclasses) -------------------------------------- #
    def _build_sample_expr(self, index: int, check: Any) -> pl.Expr:
        """The struct projected for a sample row (must include a ``line`` field)."""
        raise NotImplementedError

    def _sample_payload(self, check: Any, rec: dict) -> Any:
        """Turn one collected sample struct into the stored value(s)."""
        raise NotImplementedError

    def _assemble(self) -> Any:
        """Shape the accumulated results for the report."""
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Column checks: + per-column failing-row count, regrouped by column
# --------------------------------------------------------------------------- #
class ColumnRunner(MaskProcessor):
    """Per-column checks. Adds the per-column failing-row count on top of the base."""

    def __init__(self, checks_by_column: dict[str, list[BoundCheck]], sample_size: int,
                 engine: str = "streaming") -> None:
        flat = [chk for chks in checks_by_column.values() for chk in chks]
        super().__init__(flat, sample_size, engine)          # base handles masks/counts/samples
        self._col_indices = self._group_by_column()          # column -> its check indices
        self._colfail_exprs = self._make_colfail_exprs()
        self._colfail = {col: 0 for col in self._col_indices}

    def _group_by_column(self) -> dict[str, list[int]]:
        indices: dict[str, list[int]] = {}
        for i, chk in enumerate(self._checks):
            indices.setdefault(chk.column, []).append(i)
        return indices

    def _make_colfail_exprs(self) -> list[pl.Expr]:
        """One failing-row count per column (a row failing several checks counts once)."""
        return [
            pl.any_horizontal([pl.col(f"m{k}") for k in idxs]).sum().alias(f"colfail:{col}")
            for col, idxs in self._col_indices.items()
        ]

    # extend the base collect + accumulation with the per-column supplement
    def _aggregates(self) -> list[pl.Expr]:
        return [*super()._aggregates(), *self._colfail_exprs]

    def _accumulate(self, row: dict, offset: int) -> None:
        super()._accumulate(row, offset)
        for col in self._colfail:
            self._colfail[col] += int(row[f"colfail:{col}"] or 0)

    # variation points
    def _build_sample_expr(self, index: int, check: BoundCheck) -> pl.Expr:
        return pl.struct(
            (pl.col(ROW_IDX) + 1).alias("line"),
            pl.col(check.column).cast(pl.Utf8).alias("value"),
        )

    def _sample_payload(self, check: BoundCheck, rec: dict) -> str:
        value = rec["value"]
        return value if value is not None else ""

    def _assemble(self) -> list[ColumnData]:
        """Regroup the flat results under their column, in schema order."""
        return [
            (col, self._colfail[col],
             [(self._checks[i].check, self._counts[i], self._samples[i]) for i in idxs])
            for col, idxs in self._col_indices.items()
        ]


# --------------------------------------------------------------------------- #
# Row checks: cross-column; sample shows the involved columns; flat result
# --------------------------------------------------------------------------- #
class RowRunner(MaskProcessor):
    """Cross-column integrity checks. Nearly empty — only the two variation points."""

    def __init__(self, checks: list[RowCheck], sample_size: int, engine: str = "streaming") -> None:
        super().__init__(checks, sample_size, engine)

    def _build_sample_expr(self, index: int, check: RowCheck) -> pl.Expr:
        return pl.struct(
            (pl.col(ROW_IDX) + 1).alias("line"),
            *[pl.col(c).cast(pl.Utf8).alias(c) for c in check.columns],
        )

    def _sample_payload(self, check: RowCheck, rec: dict) -> dict[str, str]:
        return {c: (rec[c] if rec[c] is not None else "") for c in check.columns}

    def _assemble(self) -> list[RowData]:
        return [(chk.name, self._counts[i], self._samples[i]) for i, chk in enumerate(self._checks)]
