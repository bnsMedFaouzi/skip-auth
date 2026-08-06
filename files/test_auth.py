#!/usr/bin/env python3
"""Convert an inventory XSD into the JSON schema consumed by csv_validator.

Standalone: uses only the standard library and does NOT import the csv_validator
package. It reads an .xsd whose columns are declared as <xs:element> (either with
an inline <xs:simpleType>/<xs:restriction> or a type="<named>" reference), and
emits JSON with `definitions` (named simpleTypes) and `properties` (columns, in
document order), using the source keys the JSON parser understands (Size,
TotalDigit, FractionDigit, AuthorizeValue, Mandatory, ColumnIndex, pattern...).

Usage:
    python xsd_to_json.py input.xsd output.json

Mapping (documented, so you can eyeball it):
  base xs:string                    -> "string"
  base xs:decimal/float/double      -> "number"   (+ TotalDigit/FractionDigit)
  base xs:integer/int/long/short    -> "integer"
  base xs:date                      -> "date"
  base xs:dateTime                  -> "timestamp"
  base xs:boolean                   -> "boolean"
  type="Foo" (no xs: builtin)       -> "Foo"      (a definitions key)

  xs:maxLength    -> Size
  xs:totalDigits  -> TotalDigit
  xs:fractionDigits -> FractionDigit
  xs:enumeration  -> AuthorizeValue (list)
  xs:pattern      -> pattern
  xs:minInclusive -> minimum
  nillable="false" -> Mandatory "Yes"   |   otherwise -> "No"
  document order of the column elements -> ColumnIndex (1-based)

Note: an XSD `xs:date`/`xs:dateTime` says the *logical* type, not the textual
CSV format (e.g. "yyyyMMdd"). This script therefore does NOT emit a `Format`;
set the engine's default_date_format / default_timestamp_format instead, or add
Format by hand where a column needs a specific one.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET

XSD_NS = "http://www.w3.org/2001/XMLSchema"

# XSD builtin base types -> engine primitive type token.
_BUILTIN = {
    "string": "string", "normalizedString": "string", "token": "string",
    "decimal": "number", "double": "number", "float": "number",
    "integer": "integer", "int": "integer", "long": "integer",
    "short": "integer", "nonNegativeInteger": "integer", "positiveInteger": "integer",
    "date": "date",
    "dateTime": "timestamp",
    "boolean": "boolean",
}


def _local(tag: str) -> str:
    """Local name of a possibly namespaced tag or attribute value."""
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _facets(restriction: ET.Element) -> dict:
    """Read an <xs:restriction> into the source keys the parser understands."""
    out: dict = {}
    base = _local(restriction.get("base", ""))
    out["type"] = _BUILTIN.get(base, base)  # unknown base name -> a definitions key

    enum: list[str] = []
    for facet in restriction:
        name = _local(facet.tag)
        value = facet.get("value")
        if name == "maxLength":
            out["Size"] = int(value)
        elif name == "totalDigits":
            out["TotalDigit"] = int(value)
        elif name == "fractionDigits":
            out["FractionDigit"] = int(value)
        elif name == "pattern":
            out["pattern"] = value
        elif name == "minInclusive":
            out["minimum"] = float(value)
        elif name == "enumeration":
            enum.append(value)
    if enum:
        out["AuthorizeValue"] = enum
    return out


def _restriction_of(node: ET.Element) -> ET.Element | None:
    """Return the <xs:restriction> under an element/simpleType, if any."""
    for st in node:
        if _local(st.tag) == "simpleType":
            for r in st:
                if _local(r.tag) == "restriction":
                    return r
    return None


def _column(element: ET.Element, index: int) -> dict:
    """Convert one column <xs:element> into a property dict."""
    prop: dict = {}
    typed = element.get("type")
    restriction = _restriction_of(element)

    if restriction is not None:
        prop.update(_facets(restriction))
    elif typed is not None:
        base = _local(typed)
        prop["type"] = _BUILTIN.get(base, base)  # named type -> definitions key
    else:
        prop["type"] = "string"  # bare element, no restriction: treat as free text

    prop["Mandatory"] = "No" if element.get("nillable", "true") == "true" else "Yes"
    prop["ColumnIndex"] = index
    return prop


def convert(xsd_path: str) -> dict:
    """Parse the XSD and return the {definitions, properties} JSON structure."""
    root = ET.parse(xsd_path).getroot()

    # definitions = every named simpleType declared anywhere in the file.
    definitions: dict = {}
    for st in root.iter(f"{{{XSD_NS}}}simpleType"):
        name = st.get("name")
        if not name:
            continue
        for r in st:
            if _local(r.tag) == "restriction":
                definitions[name] = _facets(r)

    # properties = the column elements, in document order.
    # A "column" is a named xs:element that either carries an inline restriction
    # or a type reference (this skips the schema's structural wrapper elements).
    properties: dict = {}
    index = 0
    for el in root.iter(f"{{{XSD_NS}}}element"):
        name = el.get("name")
        if not name:
            continue
        if el.get("type") is None and _restriction_of(el) is None:
            continue
        index += 1
        properties[name] = _column(el, index)

    return {"definitions": definitions, "properties": properties}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python xsd_to_json.py input.xsd output.json", file=sys.stderr)
        return 2
    schema = convert(argv[1])
    with open(argv[2], "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2, ensure_ascii=False)
    print(f"{len(schema['properties'])} columns, "
          f"{len(schema['definitions'])} definitions -> {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
