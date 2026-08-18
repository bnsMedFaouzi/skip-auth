"""PROTOTYPE — structure checks with a registry, mirroring rows and columns.

Same shape as the row side:
    RowConstraint (ABC)          ->  StructureCheck (ABC)
    Compare, RequiredIf, ...      ->  HeaderCheck, MaxColumns, ...   (typed classes)
    RowConstraintRegistry        ->  StructureCheckRegistry
    default_row_registry()       ->  default_structure_registry()
    activated by "rowConstraints"->  activated by "structureChecks"

The JSON declares which structure checks to apply; the registry maps `kind` -> class,
reads the params via `from_dict`, VALIDATES (unknown kind / missing param) before
adding, and returns the check instances the FileRunner runs. Not wired into the
package (StructureIssue is a plain dataclass here; it would be the model on merge).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from csv_validator.models import ColumnDef, EngineConfig   # existing


@dataclass
class StructureIssue:
    check: str
    code: str
    message: str
    columns: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# base — mirrors RowConstraint
# --------------------------------------------------------------------------- #
class StructureCheck(ABC):
    """A file-structure check, declared by the schema and built by the registry."""

    kind: str = "structure"
    name: str = "structure"

    def issue(self, code: str, message: str, columns: list[str] | None = None) -> StructureIssue:
        return StructureIssue(check=self.name, code=code, message=message, columns=columns or [])

    @abstractmethod
    def check(self, columns: list[ColumnDef], actual: list[str], config: EngineConfig) -> list[StructureIssue]:
        """The issues this check finds, empty when the header satisfies it."""

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "StructureCheck":
        """Build a typed instance from its schema definition."""


# --------------------------------------------------------------------------- #
# concrete checks — typed, each carrying only its own params
# --------------------------------------------------------------------------- #
class HeaderCheck(StructureCheck):
    """The CSV columns must match the schema: presence, no extras, and order."""

    kind = "header"
    name = "header"

    def check(self, columns, actual, config):
        expected = [c.name for c in columns]
        expected_set, actual_set = set(expected), set(actual)
        issues: list[StructureIssue] = []

        missing = [c for c in expected if c not in actual_set]
        if missing:
            issues.append(self.issue("missing_columns", f"missing columns: {', '.join(missing)}", missing))

        unexpected = [c for c in actual if c not in expected_set]
        if unexpected and not config.allow_extra_columns:
            issues.append(self.issue("unexpected_columns",
                                     f"unexpected columns: {', '.join(unexpected)}", unexpected))

        if config.strict_column_order and not missing and (config.allow_extra_columns or not unexpected):
            if [c for c in actual if c in expected_set] != expected:
                issues.append(self.issue("out_of_order", "columns out of order"))
        return issues

    @classmethod
    def from_dict(cls, d: dict) -> "HeaderCheck":
        return cls()


@dataclass
class MaxColumns(StructureCheck):
    """The CSV must not have more than `limit` columns."""

    kind = "maxColumns"
    name = "max_columns"
    limit: int

    def check(self, columns, actual, config):
        if len(actual) > self.limit:
            return [self.issue("too_many_columns", f"too many columns: {len(actual)} > {self.limit}")]
        return []

    @classmethod
    def from_dict(cls, d: dict) -> "MaxColumns":
        if "limit" not in d:
            raise ValueError("maxColumns: 'limit' is required")
        return cls(limit=int(d["limit"]))


# --------------------------------------------------------------------------- #
# registry — mirrors RowConstraintRegistry
# --------------------------------------------------------------------------- #
class StructureCheckRegistry:
    """Holds the known structure-check classes (built-in + custom) and builds them."""

    def __init__(self) -> None:
        self._by_kind: dict[str, type[StructureCheck]] = {}

    def register(self, check_cls: type[StructureCheck]) -> "StructureCheckRegistry":
        self._by_kind[check_cls.kind] = check_cls
        return self

    def build(self, definitions: list[dict]) -> list[StructureCheck]:
        """Turn the schema's structure-check definitions into check instances.

        Validates each: the `kind` must be known, and `from_dict` validates the
        params — anything else raises a clear error, like the parser.
        """
        checks: list[StructureCheck] = []
        for d in definitions:
            kind = d.get("kind")
            cls = self._by_kind.get(kind)
            if cls is None:
                raise ValueError(f"unknown structure check kind: {kind!r}")
            checks.append(cls.from_dict(d))
        return checks


def default_structure_registry() -> StructureCheckRegistry:
    """The built-in structure checks (extend with `.register(MyCheck)`)."""
    reg = StructureCheckRegistry()
    for cls in (HeaderCheck, MaxColumns):
        reg.register(cls)
    return reg
