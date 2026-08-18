"""PROTOTYPE — row constraints as typed classes, mirroring column constraints.

Symmetry with the column side:
    Constraint (ABC)         ->  RowConstraint (ABC)
    Minimum, MaxLength, ...  ->  Compare, RequiredIf, Equals, MutuallyRequired  (typed dataclasses)
    ValidatorRegistry        ->  RowConstraintRegistry
    produces BoundCheck      ->  produces RowCheck

Each constraint is a dataclass carrying ONLY its own parameters (no generic dict),
and knows how to produce its involved `columns()` (for the sample) and its
`invalid()` Polars mask (True = the row violates). `to_check()` wraps it into the
`RowCheck` consumed by `RowRunner`. Adding a new kind = a new dataclass + register.
Not wired into the package.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import polars as pl

from mask_processors import RowCheck   # prototype dataclass: name / columns / invalid


# --------------------------------------------------------------------------- #
# helpers: read a CSV cell (Utf8) as a typed value for comparisons
# --------------------------------------------------------------------------- #
_OPS = {
    ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
}


def _typed(name: str, cast: str | None) -> pl.Expr:
    """Column `name` (stored as Utf8) coerced to the type needed for a comparison."""
    e = pl.col(name).cast(pl.Utf8)
    if cast == "date":
        return e.str.to_date(strict=False)
    if cast == "timestamp":
        return e.str.to_datetime(strict=False)
    if cast in ("number", "integer"):
        return e.cast(pl.Float64 if cast == "number" else pl.Int64, strict=False)
    return e                                                        # plain string compare


# --------------------------------------------------------------------------- #
# base
# --------------------------------------------------------------------------- #
class RowConstraint(ABC):
    """A cross-column integrity rule, declared by the schema. Mirrors `Constraint`."""

    kind: str = "row"
    name: str

    @abstractmethod
    def columns(self) -> list[str]:
        """Columns this rule involves (shown in the sample)."""

    @abstractmethod
    def invalid(self) -> pl.Expr:
        """Boolean mask, True where a row violates the rule."""

    def to_check(self) -> RowCheck:
        """Wrap into the RowCheck consumed by the batch processor."""
        return RowCheck(name=self.name, columns=self.columns(), invalid=self.invalid())

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "RowConstraint":
        """Build a typed instance from its schema definition."""


# --------------------------------------------------------------------------- #
# concrete, typed constraints — each carries only its own parameters
# --------------------------------------------------------------------------- #
@dataclass
class Compare(RowConstraint):
    """`left op right` must hold on each row (e.g. EndDate >= StartDate)."""

    kind = "compare"
    name: str
    left: str
    op: str
    right: str
    cast: str | None = None          # "date" / "number" / "integer" / None (string)

    def columns(self) -> list[str]:
        return [self.left, self.right]

    def invalid(self) -> pl.Expr:
        rule_ok = _OPS[self.op](_typed(self.left, self.cast), _typed(self.right, self.cast))
        return ~rule_ok               # violation = rule does not hold (null -> not flagged)

    @classmethod
    def from_dict(cls, d: dict) -> "Compare":
        if d["op"] not in _OPS:
            raise ValueError(f"compare: unknown op {d['op']!r}")
        return cls(name=d["name"], left=d["left"], op=d["op"], right=d["right"], cast=d.get("cast"))


@dataclass
class RequiredIf(RowConstraint):
    """If `when_col == equals`, then `require` must be present (non-empty)."""

    kind = "requiredIf"
    name: str
    when_col: str
    equals: str
    require: str

    def columns(self) -> list[str]:
        return [self.when_col, self.require]

    def invalid(self) -> pl.Expr:
        req = pl.col(self.require).cast(pl.Utf8)
        missing = req.is_null() | (req.str.len_chars() == 0)
        return (pl.col(self.when_col).cast(pl.Utf8) == self.equals) & missing

    @classmethod
    def from_dict(cls, d: dict) -> "RequiredIf":
        return cls(name=d["name"], when_col=d["whenCol"], equals=d["equals"], require=d["require"])


# --------------------------------------------------------------------------- #
# registry: kind -> class (mirrors ValidatorRegistry / default_registry)
@dataclass
class Equals(RowConstraint):
    """Two columns must hold the same value on each row (e.g. Ccy == SettlementCcy)."""

    kind = "equals"
    name: str
    left: str
    right: str

    def columns(self) -> list[str]:
        return [self.left, self.right]

    def invalid(self) -> pl.Expr:
        return pl.col(self.left).cast(pl.Utf8) != pl.col(self.right).cast(pl.Utf8)

    @classmethod
    def from_dict(cls, d: dict) -> "Equals":
        return cls(name=d["name"], left=d["left"], right=d["right"])


@dataclass
class MutuallyRequired(RowConstraint):
    """Two columns must be present together or absent together (not one without the other)."""

    kind = "mutuallyRequired"
    name: str
    left: str
    right: str

    def columns(self) -> list[str]:
        return [self.left, self.right]

    def invalid(self) -> pl.Expr:
        def filled(c: str) -> pl.Expr:
            v = pl.col(c).cast(pl.Utf8)
            return v.is_not_null() & (v.str.len_chars() > 0)
        return filled(self.left) != filled(self.right)          # exactly one filled -> violation

    @classmethod
    def from_dict(cls, d: dict) -> "MutuallyRequired":
        return cls(name=d["name"], left=d["left"], right=d["right"])


# --------------------------------------------------------------------------- #
class RowConstraintRegistry:
    """Holds the known constraint classes (built-in + custom) and builds RowChecks."""

    def __init__(self) -> None:
        self._by_kind: dict[str, type[RowConstraint]] = {}

    def register(self, constraint_cls: type[RowConstraint]) -> "RowConstraintRegistry":
        """Register a constraint class by its `kind`. Returns self for chaining."""
        self._by_kind[constraint_cls.kind] = constraint_cls
        return self

    def build(self, definitions: list[dict], columns: list[str]) -> list[RowCheck]:
        """Turn the schema's row-constraint definitions into RowChecks.

        Each definition is resolved to its typed constraint, then validated: the
        `kind` must be known and every column it references must exist in the
        schema (`columns`). Anything else raises a clear error, like the parser.
        """
        known = set(columns)
        checks: list[RowCheck] = []
        for d in definitions:
            kind = d.get("kind")
            cls = self._by_kind.get(kind)
            if cls is None:
                raise ValueError(f"unknown row constraint kind: {kind!r}")
            constraint = cls.from_dict(d)
            missing = [c for c in constraint.columns() if c not in known]
            if missing:
                raise ValueError(
                    f"row constraint {constraint.name!r}: unknown column(s) {', '.join(missing)}"
                )
            checks.append(constraint.to_check())
        return checks


def default_row_registry() -> RowConstraintRegistry:
    """The built-in constraints (extend with `.register(MyConstraint)`)."""
    reg = RowConstraintRegistry()
    for cls in (Compare, RequiredIf, Equals, MutuallyRequired):
        reg.register(cls)
    return reg
