"""PROTOTYPE (row) — same mechanism as the column registry.

  Column validators                Row constraints
  register INSTANCES (Minimum())   register INSTANCES (Compare())
  applies(col) / build(col)        applies(defn) / build(defn)
  read params from ColumnDef       read params from a generic Definition

`Definition` is a single generic type (kind + params) — reused later for structure.
Each constraint is a stateless builder: `applies(defn)` says whether it handles that
kind, `build(defn)` reads the params and returns a RowCheck. The registry holds a
LIST of instances and iterates with applies (exactly like columns). Not wired in.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import polars as pl

from mask_processors import RowCheck   # prototype dataclass: name / columns / invalid


# generic definition (shared later with structure) -- Q2 option C
@dataclass
class Definition:
    """A declared rule from the schema: its `kind` and its raw `params`."""

    kind: str
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Definition":
        d = dict(d)
        return cls(kind=d.pop("kind"), params=d)


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


# base -- a stateless builder, registered as an instance (like a column validator)
class RowConstraint(ABC):
    """Builds a RowCheck from a Definition. Instances are registered, not classes."""

    kind: str = "row"

    def applies(self, defn: Definition) -> bool:
        """Whether this constraint handles that definition (by default, by kind)."""
        return defn.kind == self.kind

    @abstractmethod
    def build(self, defn: Definition) -> RowCheck:
        """Read the definition's params and return the RowCheck to run."""


# concrete constraints (stateless -- params come from the Definition)
class Compare(RowConstraint):
    """`left op right` must hold (e.g. EndDate >= StartDate)."""

    kind = "compare"

    def build(self, defn: Definition) -> RowCheck:
        p = defn.params
        left, op, right, cast = p["left"], p["op"], p["right"], p.get("cast")
        if op not in _OPS:
            raise ValueError(f"compare: unknown op {op!r}")
        rule_ok = _OPS[op](_typed(left, cast), _typed(right, cast))
        return RowCheck(name=p["name"], columns=[left, right], invalid=~rule_ok)


class RequiredIf(RowConstraint):
    """If `whenCol == equals`, then `require` must be present (non-empty)."""

    kind = "requiredIf"

    def build(self, defn: Definition) -> RowCheck:
        p = defn.params
        when_col, equals, require = p["whenCol"], p["equals"], p["require"]
        req = pl.col(require).cast(pl.Utf8)
        missing = req.is_null() | (req.str.len_chars() == 0)
        invalid = (pl.col(when_col).cast(pl.Utf8) == equals) & missing
        return RowCheck(name=p["name"], columns=[when_col, require], invalid=invalid)


class Equals(RowConstraint):
    """Two columns must hold the same value (e.g. Ccy == SettlementCcy)."""

    kind = "equals"

    def build(self, defn: Definition) -> RowCheck:
        p = defn.params
        left, right = p["left"], p["right"]
        invalid = pl.col(left).cast(pl.Utf8) != pl.col(right).cast(pl.Utf8)
        return RowCheck(name=p["name"], columns=[left, right], invalid=invalid)


class MutuallyRequired(RowConstraint):
    """Two columns must be present together or absent together."""

    kind = "mutuallyRequired"

    def build(self, defn: Definition) -> RowCheck:
        p = defn.params
        left, right = p["left"], p["right"]

        def filled(c: str) -> pl.Expr:
            v = pl.col(c).cast(pl.Utf8)
            return v.is_not_null() & (v.str.len_chars() > 0)

        invalid = filled(left) != filled(right)                # exactly one filled -> violation
        return RowCheck(name=p["name"], columns=[left, right], invalid=invalid)


# registry -- list of instances, iterate with applies (exactly like columns)
class RowConstraintRegistry:
    """Holds constraint instances (built-in + custom) and builds RowChecks."""

    def __init__(self) -> None:
        self._units: list[RowConstraint] = []

    def register(self, constraint: RowConstraint) -> "RowConstraintRegistry":
        """Register a constraint instance. Returns self for chaining."""
        self._units.append(constraint)
        return self

    def build(self, definitions: list[Definition], columns: list[str]) -> list[RowCheck]:
        """Build the RowChecks; validate the kind is known and the columns exist."""
        known = set(columns)
        checks: list[RowCheck] = []
        for defn in definitions:
            unit = next((u for u in self._units if u.applies(defn)), None)
            if unit is None:
                raise ValueError(f"unknown row constraint kind: {defn.kind!r}")
            check = unit.build(defn)
            missing = [c for c in check.columns if c not in known]
            if missing:
                raise ValueError(f"row constraint {check.name!r}: unknown column(s) {', '.join(missing)}")
            checks.append(check)
        return checks


def default_row_registry() -> RowConstraintRegistry:
    """The built-in constraints (extend with `.register(MyConstraint())`)."""
    reg = RowConstraintRegistry()
    for unit in (Compare(), RequiredIf(), Equals(), MutuallyRequired()):
        reg.register(unit)
    return reg
