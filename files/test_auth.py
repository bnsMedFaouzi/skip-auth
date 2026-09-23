"""PROTOTYPE — single-pass CSV source; each provider yields LINES.

The origin of the bytes is hidden behind a provider that exposes a line reader:
  - FileProvider   -> iterates the file handle (native line iteration)
  - StreamProvider -> uses boto3 StreamingBody.iter_lines() (line-aware, not chunks)

Both yield lines WITHOUT the trailing newline (normalized); the source rejoins with
b"\\n" when rebuilding a block, so iter_frames is agnostic to the origin. One open,
header read from the same line iterator, one close at the end. Not wired in.
"""

from __future__ import annotations

import io
import itertools
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

import polars as pl


# --------------------------------------------------------------------------- #
# providers: each returns a line reader (iterate -> lines without trailing \n)
# --------------------------------------------------------------------------- #
class LineReader(ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[bytes]: ...
    @abstractmethod
    def close(self) -> None: ...


class ByteStreamProvider(ABC):
    @abstractmethod
    def open(self) -> LineReader: ...
    @property
    @abstractmethod
    def name(self) -> str: ...


class _FileLines(LineReader):
    def __init__(self, fh) -> None:
        self._fh = fh

    def __iter__(self):
        for line in self._fh:                       # file iterates by line natively
            yield line.rstrip(b"\r\n")              # normalize: drop trailing newline

    def close(self):
        self._fh.close()


class FileProvider(ByteStreamProvider):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def open(self) -> LineReader:
        return _FileLines(open(self._path, "rb"))

    @property
    def name(self) -> str:
        return self._path.name


class _StreamLines(LineReader):
    def __init__(self, body) -> None:
        self._body = body

    def __iter__(self):
        return iter(self._body.iter_lines())        # boto3: line-aware (already stripped)

    def close(self):
        self._body.close()                          # release the HTTP connection


class StreamProvider(ByteStreamProvider):
    """Wraps a boto3 StreamingBody (read-once); uses its iter_lines()."""

    def __init__(self, body, name: str) -> None:
        self._body = body
        self._name = name

    def open(self) -> LineReader:
        return _StreamLines(self._body)

    @property
    def name(self) -> str:
        return self._name


# --------------------------------------------------------------------------- #
# single-pass CSV source
# --------------------------------------------------------------------------- #
class CsvDataSource:
    """CSV read in one pass; provider yields lines, blocks rebuilt with b'\\n'."""

    def __init__(self, provider: ByteStreamProvider, *, separator: str = ";") -> None:
        self._provider = provider
        self._separator = separator
        self._reader: LineReader | None = None
        self._lines: Iterator[bytes] | None = None
        self._header_line: bytes | None = None
        self._columns: list[str] | None = None
        self._closed = False

    @property
    def name(self) -> str:
        return self._provider.name

    # -- lifecycle: context manager (recommended) + idempotent close --------- #
    def __enter__(self) -> "CsvDataSource":
        self._ensure_open()
        return self

    def __exit__(self, *exc) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
            self._reader = None
        self._lines = None
        self._closed = True

    # -- one open, header read from the same line iterator ------------------- #
    def _ensure_open(self) -> None:
        if self._reader is not None:
            return
        if self._closed:
            raise RuntimeError("data source already consumed/closed (single-pass)")
        self._reader = self._provider.open()
        self._lines = iter(self._reader)
        self._header_line = next(self._lines, b"")            # first line = header
        raw = self._parse_header(self._header_line)
        self._columns = raw[:-1] if (raw and raw[-1].strip() == "") else raw

    def _parse_header(self, header_line: bytes) -> list[str]:
        return pl.read_csv(io.BytesIO(header_line), separator=self._separator,
                           has_header=True, infer_schema_length=0).columns

    def _scan(self, buf: io.BytesIO) -> pl.LazyFrame:
        return pl.scan_csv(buf, separator=self._separator, infer_schema_length=0,
                           null_values=[], low_memory=True)

    # -- public API --------------------------------------------------------- #
    def columns(self) -> list[str]:
        if self._columns is None:
            self._ensure_open()
        return self._columns

    def iter_frames(self, batch_size: int) -> Iterator[pl.LazyFrame]:
        """Yield lazy scans of `batch_size` rows; blocks rebuilt as header + lines."""
        self._ensure_open()
        keep = self._columns
        try:
            while True:
                block = list(itertools.islice(self._lines, batch_size))   # agnostic: just lines
                if not block:
                    break
                buf = io.BytesIO(b"\n".join([self._header_line, *block]) + b"\n")  # rejoin with \n
                yield self._scan(buf).select(keep)
        finally:
            self.close()                                        # safety net
