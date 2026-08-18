"""PROTOTYPE (row) — typed constraint definitions + a column-style registry.

Definitions are typed dataclasses (Compare(left, op, right), ...), each with
from_dict / columns() / invalid() / to_check() — same as before.

The registry behaves like the column one: a LIST of registered units, `register`,
and selection by ITERATING and asking `applies(...)` (not a dict lookup by kind).
The one inherent difference: column registers stateless INSTANCES (params live on
ColumnDef), while a row constraint carries its own params, so we register the
CLASSES and `applies` is a classmethod. The mechanics are otherwise identical.
Not wired into the package.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import polars as pl

from mask_processors import RowCheck   # prototype dataclass: name / columns / invalid


_OPS = {
    ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
}


def _typed(name: str, cast: str | None) -> pl.Expr:
    """Column `name` (Utf8) coerced to the type needed for a comparison."""
    e = pl.col(name).cast(pl.Utf8)
    if cast == "date":
        return e.str.to_date(strict=False)
    if cast == "timestamp":
        return e.str.to_datetime(strict=False)
    if cast in ("number", "integer"):
        return e.cast(pl.Float64 if cast == "number" else pl.Int64, strict=False)
    return e


# --------------------------------------------------------------------------- #
# base (mirrors Constraint; `applies` mirrors the column validator's applies)
# --------------------------------------------------------------------------- #
class RowConstraint(ABC):
    """A typed cross-column rule. Registered classes are selected via `applies`."""

    kind = "row"

    @classmethod
    def applies(cls, d: dict) -> bool:
        """Whether this constraint handles that definition (by default, by kind)."""
        return d.get("kind") == cls.kind

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "RowConstraint":
        """Build the typed instance from its schema definition."""

    @abstractmethod
    def columns(self) -> list[str]:
        """Columns this rule involves (for the sample)."""

    @abstractmethod
    def invalid(self) -> pl.Expr:
        """Boolean mask, True where a row violates the rule."""

    def to_check(self) -> RowCheck:
        return RowCheck(name=self.name, columns=self.columns(), invalid=self.invalid())


# --------------------------------------------------------------------------- #
# typed constraints (definitions as before)
# --------------------------------------------------------------------------- #
@dataclass
class Compare(RowConstraint):
    """`left op right` must hold (e.g. EndDate >= StartDate)."""

    kind = "compare"
    name: str
    left: str
    op: str
    right: str
    cast: str | None = None

    def columns(self): return [self.left, self.right]

    def invalid(self):
        if self.op not in _OPS:
            raise ValueError(f"compare: unknown op {self.op!r}")
        return ~_OPS[self.op](_typed(self.left, self.cast), _typed(self.right, self.cast))

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], left=d["left"], op=d["op"], right=d["right"], cast=d.get("cast"))


@dataclass
class RequiredIf(RowConstraint):
    """If `when_col == equals`, then `require` must be present (non-empty)."""

    kind = "requiredIf"
    name: str
    when_col: str
    equals: str
    require: str

    def columns(self): return [self.when_col, self.require]

    def invalid(self):
        req = pl.col(self.require).cast(pl.Utf8)
        missing = req.is_null() | (req.str.len_chars() == 0)
        return (pl.col(self.when_col).cast(pl.Utf8) == self.equals) & missing

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], when_col=d["whenCol"], equals=d["equals"], require=d["require"])


@dataclass
class Equals(RowConstraint):
    """Two columns must hold the same value (e.g. Ccy == SettlementCcy)."""

    kind = "equals"
    name: str
    left: str
    right: str

    def columns(self): return [self.left, self.right]

    def invalid(self):
        return pl.col(self.left).cast(pl.Utf8) != pl.col(self.right).cast(pl.Utf8)

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], left=d["left"], right=d["right"])


@dataclass
class MutuallyRequired(RowConstraint):
    """Two columns must be present together or absent together."""

    kind = "mutuallyRequired"
    name: str
    left: str
    right: str

    def columns(self): return [self.left, self.right]

    def invalid(self):
        def filled(c):
            v = pl.col(c).cast(pl.Utf8)
            return v.is_not_null() & (v.str.len_chars() > 0)
        return filled(self.left) != filled(self.right)

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], left=d["left"], right=d["right"])


# --------------------------------------------------------------------------- #
# registry — list + register + iterate with applies (like the column registry)
# --------------------------------------------------------------------------- #
class RowConstraintRegistry:
    """Holds constraint classes (built-in + custom) and builds RowChecks."""

    def __init__(self) -> None:
        self._units: list[type[RowConstraint]] = []

    def register(self, constraint_cls: type[RowConstraint]) -> "RowConstraintRegistry":
        """Register a constraint class. Returns self for chaining."""
        self._units.append(constraint_cls)
        return self

    def build(self, definitions: list[dict], columns: list[str]) -> list[RowCheck]:
        """Build the RowChecks; validate the kind is known and the columns exist."""
        known = set(columns)
        checks: list[RowCheck] = []
        for d in definitions:
            cls = next((u for u in self._units if u.applies(d)), None)   # like column: iterate + applies
            if cls is None:
                raise ValueError(f"unknown row constraint kind: {d.get('kind')!r}")
            constraint = cls.from_dict(d)
            missing = [c for c in constraint.columns() if c not in known]
            if missing:
                raise ValueError(f"row constraint {constraint.name!r}: unknown column(s) {', '.join(missing)}")
            checks.append(constraint.to_check())
        return checks


def default_row_registry() -> RowConstraintRegistry:
    """The built-in constraints (extend with `.register(MyConstraint)`)."""
    reg = RowConstraintRegistry()
    for cls in (Compare, RequiredIf, Equals, MutuallyRequired):
        reg.register(cls)
    return reg
