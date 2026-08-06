"""Engine configuration (Pydantic)."""

from __future__ import annotations

from pydantic import BaseModel


class EngineConfig(BaseModel):
    """Centralized engine parameters."""

    sample_size: int = 20            # bounded error sample per check
    streaming: bool = True           # use the Polars streaming engine

    # header / file structure
    strict_column_order: bool = True     # columns must match the schema order
    header_gate: bool = True             # invalid header stops value validation
    allow_extra_columns: bool = False    # tolerate CSV columns not in the schema

    # default date/timestamp formats, used when a column does not provide one
    default_date_format: str = "%Y-%m-%d"
    default_timestamp_format: str = "%Y-%m-%dT%H:%M:%S"

    # Rows per batch: bounds peak memory (a batch is evaluated then discarded).
    # Leave as None to size it automatically from the column count so peak memory
    # stays near `target_memory_mb` whatever the schema width; set an int to force it.
    row_batch_size: int | None = None
    target_memory_mb: int = 300          # memory budget used when auto-sizing the batch

    @property
    def engine_mode(self) -> str:
        """The Polars collect engine: streaming when enabled, else auto."""
        return "streaming" if self.streaming else "auto"

    def batch_for(self, num_columns: int) -> int:
        """Rows per batch for a schema of `num_columns` columns.

        Returns `row_batch_size` if set. Otherwise sizes the batch so peak memory
        stays near `target_memory_mb`: peak grows with (rows x columns), so the
        row count is scaled down as the schema widens. Clamped to a safe range.
        """
        if self.row_batch_size is not None:
            return self.row_batch_size
        budget_bytes = max(self.target_memory_mb - _BASELINE_MB, 50) * 1_000_000
        rows = int(budget_bytes / (_BYTES_PER_CELL * max(num_columns, 1)))
        return max(_MIN_BATCH, min(rows, _MAX_BATCH))

    def estimated_peak_mb(self, num_columns: int, rows_in_memory: int | None = None) -> float:
        """A-priori peak-memory estimate (MB), the inverse of `batch_for`.

        With streaming, only one batch is held at a time, so peak depends on the
        batch size (used by default here) and the column count — NOT the total row
        count. Pass `rows_in_memory` (e.g. the whole file's row count) to estimate
        the in-memory case instead. Only as accurate as the calibration constants.
        """
        rows = rows_in_memory if rows_in_memory is not None else self.batch_for(num_columns)
        return _BASELINE_MB + _BYTES_PER_CELL * rows * max(num_columns, 1) / 1_000_000


# Empirical peak-memory model (measured): peak ~= baseline + bytes/cell * rows * cols.
_BASELINE_MB = 60        # interpreter + Polars + one small block
_BYTES_PER_CELL = 55     # per (row x column) at peak: Utf8 block + bool masks + intermediates
_MIN_BATCH = 5_000       # keep some batching efficiency on very wide schemas
_MAX_BATCH = 200_000     # cap on very narrow schemas
