"""PROTOTYPE — single-pass CSV source over a pluggable byte provider.

The origin of the bytes (local file or an S3/COS StreamingBody) is hidden behind
a ByteStreamProvider. The source opens the stream ONCE and, from that single
handle, in order: reads the header line (-> columns), then yields row blocks.
Works identically for a re-openable file and a read-once stream. Not wired in.
"""

from __future__ import annotations

import io
import itertools
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO

import polars as pl


# --------------------------------------------------------------------------- #
# providers: where the bytes come from
# --------------------------------------------------------------------------- #
class ByteStreamProvider(ABC):
    """Supplies a readable binary stream and a display name."""

    @abstractmethod
    def open(self) -> BinaryIO:
        """Return a readable, line-iterable binary stream (opened once by the source)."""

    @property
    @abstractmethod
    def name(self) -> str: ...


class FileProvider(ByteStreamProvider):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def open(self) -> BinaryIO:
        return open(self._path, "rb")

    @property
    def name(self) -> str:
        return self._path.name


class StreamProvider(ByteStreamProvider):
    """Wraps an already-open, read-once binary stream (e.g. boto3 StreamingBody)."""

    def __init__(self, body: BinaryIO, name: str) -> None:
        self._body = body
        self._name = name

    def open(self) -> BinaryIO:
        return self._body                      # single-use: handed out as-is

    @property
    def name(self) -> str:
        return self._name


# --------------------------------------------------------------------------- #
# single-pass CSV source
# --------------------------------------------------------------------------- #
class CsvDataSource:
    """CSV read in one pass from a byte provider, block by block, all text."""

    def __init__(self, provider: ByteStreamProvider, *, separator: str = ";") -> None:
        self._provider = provider
        self._separator = separator
        self._fh: BinaryIO | None = None          # the single open handle
        self._header_line: bytes | None = None
        self._columns: list[str] | None = None
        self._trailing_empty = False
        self._closed = False

    @property
    def name(self) -> str:
        return self._provider.name

    # -- lifecycle: context manager (recommended) + idempotent close (safety net) #
    def __enter__(self) -> "CsvDataSource":
        self._ensure_open()
        return self

    def __exit__(self, *exc) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Close the underlying stream (incl. a StreamingBody). Idempotent."""
        if self._fh is not None:
            self._fh.close()                       # the source closes what it received
            self._fh = None
        self._closed = True

    # -- one open, header read once ----------------------------------------- #
    def _ensure_open(self) -> None:
        if self._fh is not None:
            return
        if self._closed:
            raise RuntimeError("data source already consumed/closed (single-pass)")
        self._fh = self._provider.open()
        self._header_line = self._fh.readline()
        raw = self._parse_header(self._header_line)
        self._trailing_empty = bool(raw) and raw[-1].strip() == ""
        self._columns = raw[:-1] if self._trailing_empty else raw

    def _parse_header(self, header_line: bytes) -> list[str]:
        """Column names from the first line only (one tiny Polars parse; respects quoting)."""
        return pl.read_csv(io.BytesIO(header_line), separator=self._separator,
                           has_header=True, infer_schema_length=0).columns

    def _scan(self, buf: io.BytesIO) -> pl.LazyFrame:
        return pl.scan_csv(buf, separator=self._separator, infer_schema_length=0,
                           null_values=[], low_memory=True)

    # -- public API (all from the same pass) -------------------------------- #
    def columns(self) -> list[str]:
        if self._columns is None:                  # cached: readable even after close
            self._ensure_open()
        return self._columns

    def iter_frames(self, batch_size: int) -> Iterator[pl.LazyFrame]:
        """Yield lazy scans of `batch_size` rows; the first block drains the peek buffer."""
        self._ensure_open()
        keep = self._columns
        try:
            while True:
                block = list(itertools.islice(self._fh, batch_size))
                if not block:
                    break
                yield self._scan(io.BytesIO(self._header_line + b"".join(block))).select(keep)
        finally:
            self.close()                           # safety net: closes even without a `with`
