#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hard gate: compare a 1688 candidate against the target Amazon SKU.

Search results are leads, not qualified supply. This script only passes a
candidate into the profit model when product facts match or are explicitly
confirmed.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

REQUIRED_FIELDS = [
    "capacity_oz",
    "dimensions_cm",
    "pack_count",
    "lid_included",
    "microwave_safe",
    "freezer_safe",
    "dishwasher_safe",
    "food_contact_docs",
]


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))



def parse_tristate_bool(value):
    """Parse booleans strictly; ambiguous strings return None."""
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    text = str(value).strip().lower()
    if text in {"true", "yes", "y", "1", "是", "支持", "有"}:
        return True
    if text in {"false", "no", "n", "0", "否", "不支持", "无", "没有"}:
        return False
    return None


def parse_finite_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def parse_strict_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if math.isfinite(value) and value.is_integer() else None
    if isinstance(value, str):
        text = value.strip()
        return int(text) if re.fullmatch(r"[+-]?\d+", text) else None
    return None


def parse_dimensions(value):
    if isinstance(value, str):
        parts = re.split(r"[x×*]", value)
    elif isinstance(value, (list, tuple)):
        parts = list(value)
    else:
        return None
    if len(parts) != 3:
        return None
    nums = [parse_finite_number(part) for part in parts]
    return nums if all(n is not None for n in nums) else None

def compare(target: dict, candidate: dict, tolerance_cm: float = 0.5, tolerance_oz: float = 0.1) -> dict:
    tol_cm = parse_finite_number(tolerance_cm)
    tol_oz = parse_finite_number(tolerance_oz)
    if isinstance(tolerance_cm, bool) or tol_cm is None or tol_cm < 0:
        return {"qualified_for_profit_calc": False, "checks": [{"field": "tolerance_cm", "status": "INVALID", "target": None, "candidate": tolerance_cm, "note": "tolerance must be finite and >= 0"}], "blocking_count": 1, "conclusion": "NOT_QUALIFIED", "note": "invalid comparison tolerance"}
    if isinstance(tolerance_oz, bool) or tol_oz is None or tol_oz < 0:
        return {"qualified_for_profit_calc": False, "checks": [{"field": "tolerance_oz", "status": "INVALID", "target": None, "candidate": tolerance_oz, "note": "tolerance must be finite and >= 0"}], "blocking_count": 1, "conclusion": "NOT_QUALIFIED", "note": "invalid comparison tolerance"}
    checks = []

    def add(field, status, target_value=None, candidate_value=None, note=None):
        checks.append({
            "field": field,
            "status": status,
            "target": target_value,
            "candidate": candidate_value,
            "note": note,
        })

    for field in REQUIRED_FIELDS:
        if target.get(field) in (None, "", []) or candidate.get(field) in (None, "", []):
            add(field, "UNKNOWN", target.get(field), candidate.get(field), "missing required data")
            continue
        if field == "capacity_oz":
            tv, cv = parse_finite_number(target[field]), parse_finite_number(candidate[field])
            if tv is None or cv is None or tv <= 0 or cv <= 0:
                add(field, "UNKNOWN", target.get(field), candidate.get(field), "capacity must be finite and > 0")
                continue
            ok = abs(tv - cv) <= tol_oz
        elif field == "dimensions_cm":
            tv, cv = parse_dimensions(target[field]), parse_dimensions(candidate[field])
            if tv is None or cv is None or any(v <= 0 for v in tv + cv):
                add(field, "UNKNOWN", target.get(field), candidate.get(field), "dimensions must be finite and > 0")
                continue
            ok = all(abs(a - b) <= tol_cm for a, b in zip(tv, cv))
        elif field == "pack_count":
            tv, cv = parse_strict_int(target[field]), parse_strict_int(candidate[field])
            if tv is None or cv is None or tv <= 0 or cv <= 0:
                add(field, "UNKNOWN", target.get(field), candidate.get(field), "pack_count must be a positive integer")
                continue
            ok = tv == cv
        elif field in {"lid_included", "microwave_safe", "freezer_safe", "dishwasher_safe"}:
            target_bool = parse_tristate_bool(target[field])
            candidate_bool = parse_tristate_bool(candidate[field])
            if target_bool is None or candidate_bool is None:
                add(field, "UNKNOWN", target.get(field), candidate.get(field), "ambiguous boolean")
                continue
            ok = target_bool == candidate_bool and candidate_bool is True
        elif field == "food_contact_docs":
            candidate_bool = parse_tristate_bool(candidate[field])
            if candidate_bool is None:
                add(field, "UNKNOWN", target.get(field), candidate.get(field), "ambiguous boolean")
                continue
            ok = candidate_bool is True
        else:
            ok = target[field] == candidate[field]
        add(field, "PASS" if ok else "FAIL", target.get(field), candidate.get(field))

    # Optional colors: compare when both sides provide them.
    for field in ("container_color", "lid_color"):
        tv, cv = target.get(field), candidate.get(field)
        if tv or cv:
            ok = bool(tv and cv and str(tv).strip().lower() == str(cv).strip().lower())
            add(field, "PASS" if ok else ("UNKNOWN" if not tv or not cv else "FAIL"), tv, cv)

    blocking = [c for c in checks if c["status"] != "PASS"]
    return {
        "qualified_for_profit_calc": not blocking,
        "checks": checks,
        "blocking_count": len(blocking),
        "conclusion": "QUALIFIED" if not blocking else "NOT_QUALIFIED",
        "note": "A qualified result still requires sample inspection, packaging confirmation and supplier diligence.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True, help="target SKU spec JSON")
    p.add_argument("--candidate", required=True, help="1688 candidate spec JSON")
    p.add_argument("--tolerance-cm", type=float, default=0.5)
    p.add_argument("--tolerance-oz", type=float, default=0.1)
    args = p.parse_args()
    result = compare(load(args.target), load(args.candidate), args.tolerance_cm, args.tolerance_oz)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
