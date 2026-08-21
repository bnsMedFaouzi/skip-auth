"""PROTOTYPE (structure) — same pattern as rows/columns, with a global context.

Every structure check receives ONE global object (`FileContext`) that carries all
it might need: the schema columns, the actual header, the config, the file name and
the row count. So a check inspects only what it cares about (header -> columns,
notEmpty -> rows, fileName -> name) through a single, uniform argument.

Registry mirrors rows: a LIST of check classes, `register`, selection by iterating
with `applies`, construction via `from_dict`, validation before adding. The header
is just one check among others. Not wired into the package.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from csv_validator.models import ColumnDef, EngineConfig


@dataclass
class StructureIssue:
    check: str
    code: str
    message: str
    columns: list[str] = field(default_factory=list)


@dataclass
class FileContext:
    """The global object handed to every structure check (everything it may inspect)."""

    name: str                      # file / source name
    expected: list[ColumnDef]      # schema columns (normalized), in order
    actual: list[str]              # actual CSV header
    config: EngineConfig
    path: str | None = None        # file path, for early checks that peek the file
    rows: int | None = None        # row count (known after the pass; None before)


# --------------------------------------------------------------------------- #
# base (mirrors RowConstraint: classmethod applies + from_dict)
# --------------------------------------------------------------------------- #
class StructureCheck(ABC):
    """A file-structure check. Registered classes are selected via `applies`."""

    kind = "structure"
    name = "structure"

    @classmethod
    def applies(cls, d: dict) -> bool:
        return d.get("kind") == cls.kind

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "StructureCheck":
        """Build the check from its schema definition."""

    @abstractmethod
    def check(self, ctx: FileContext) -> list[StructureIssue]:
        """The issues this check finds, empty when the file satisfies it."""

    def issue(self, code: str, message: str, columns: list[str] | None = None) -> StructureIssue:
        return StructureIssue(check=self.name, code=code, message=message, columns=columns or [])


# --------------------------------------------------------------------------- #
# concrete checks — each reads only what it needs from the context
# --------------------------------------------------------------------------- #
@dataclass
class HeaderCheck(StructureCheck):
    """The CSV columns must match the schema: presence, no extras, and order.

    How it validates is declared in the JSON, not read from the global config:
    `strictOrder` (columns must be in schema order) and `allowExtra` (tolerate
    columns absent from the schema).
    """

    kind = "header"
    name = "header"
    strict_order: bool = True
    allow_extra: bool = False

    def check(self, ctx: FileContext) -> list[StructureIssue]:
        expected = [c.name for c in ctx.expected]
        expected_set, actual_set = set(expected), set(ctx.actual)
        issues: list[StructureIssue] = []

        missing = [c for c in expected if c not in actual_set]
        if missing:
            issues.append(self.issue("missing_columns", f"missing columns: {', '.join(missing)}", missing))

        unexpected = [c for c in ctx.actual if c not in expected_set]
        if unexpected and not self.allow_extra:
            issues.append(self.issue("unexpected_columns",
                                     f"unexpected columns: {', '.join(unexpected)}", unexpected))

        if self.strict_order and not missing and (self.allow_extra or not unexpected):
            if [c for c in ctx.actual if c in expected_set] != expected:
                issues.append(self.issue("out_of_order", "columns out of order"))
        return issues

    @classmethod
    def from_dict(cls, d: dict) -> "HeaderCheck":
        return cls(strict_order=bool(d.get("strictOrder", True)),
                   allow_extra=bool(d.get("allowExtra", False)))


@dataclass
class MaxColumns(StructureCheck):
    """The CSV must not have more than `limit` columns."""

    kind = "maxColumns"
    name = "max_columns"
    limit: int

    def check(self, ctx: FileContext) -> list[StructureIssue]:
        if len(ctx.actual) > self.limit:
            return [self.issue("too_many_columns", f"too many columns: {len(ctx.actual)} > {self.limit}")]
        return []

    @classmethod
    def from_dict(cls, d: dict) -> "MaxColumns":
        if "limit" not in d:
            raise ValueError("maxColumns: 'limit' is required")
        return cls(limit=int(d["limit"]))


class NotEmpty(StructureCheck):
    """The file must contain at least two lines (a header + one data row).

    An EARLY check: it peeks the file (reads at most two non-blank lines) instead
    of waiting for the post-pass row count, so it can gate before the data pass.
    """

    kind = "notEmpty"
    name = "not_empty"

    def check(self, ctx: FileContext) -> list[StructureIssue]:
        if ctx.path is None:
            return []                                          # nothing to peek
        seen = 0
        with open(ctx.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():                               # ignore blank lines
                    seen += 1
                    if seen >= 2:
                        break
        if seen < 2:
            return [self.issue("too_few_lines", "file must contain a header and at least one data row")]
        return []

    @classmethod
    def from_dict(cls, d: dict) -> "NotEmpty":
        return cls()


@dataclass
class FileNameMatches(StructureCheck):
    """The source file name must match a regex `pattern` (uses the file name)."""

    kind = "fileName"
    name = "file_name"
    pattern: str

    def check(self, ctx: FileContext) -> list[StructureIssue]:
        if re.search(self.pattern, ctx.name) is None:
            return [self.issue("bad_file_name", f"file name {ctx.name!r} does not match {self.pattern!r}")]
        return []

    @classmethod
    def from_dict(cls, d: dict) -> "FileNameMatches":
        if "pattern" not in d:
            raise ValueError("fileName: 'pattern' is required")
        return cls(pattern=d["pattern"])


# --------------------------------------------------------------------------- #
# registry — list + register + iterate with applies (like rows/columns)
# --------------------------------------------------------------------------- #
class StructureCheckRegistry:
    """Holds structure-check classes (built-in + custom) and builds them from the schema."""

    def __init__(self) -> None:
        self._units: list[type[StructureCheck]] = []

    def register(self, check_cls: type[StructureCheck]) -> "StructureCheckRegistry":
        self._units.append(check_cls)
        return self

    def build(self, definitions: list[dict]) -> list[StructureCheck]:
        """Build the checks; validate the kind is known and the params via from_dict."""
        checks: list[StructureCheck] = []
        for d in definitions:
            cls = next((u for u in self._units if u.applies(d)), None)
            if cls is None:
                raise ValueError(f"unknown structure check kind: {d.get('kind')!r}")
            checks.append(cls.from_dict(d))
        return checks


def default_structure_registry() -> StructureCheckRegistry:
    """The built-in structure checks (extend with `.register(MyCheck)`)."""
    reg = StructureCheckRegistry()
    for cls in (HeaderCheck, MaxColumns, NotEmpty, FileNameMatches):
        reg.register(cls)
    return reg
