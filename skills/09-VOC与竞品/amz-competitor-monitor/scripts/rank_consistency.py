#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalize ranking strings from different Sorftime interfaces.

Different endpoints may use different result sets and denominators. Do not
average or overwrite one rank with another; retain source, timestamp and total.
"""
from __future__ import annotations

import argparse
import json
import re



SOURCE_ALIASES = {
    "traffic": "traffic_terms",
    "traffic_terms": "traffic_terms",
    "product_traffic_terms": "traffic_terms",
    "asinrequestkeyword": "traffic_terms",
    "ranking_trend": "ranking_trend",
    "product_ranking_trend_by_keyword": "ranking_trend",
    "competitor": "competitor_keywords",
    "competitor_keywords": "competitor_keywords",
    "competitor_product_keywords": "competitor_keywords",
}


def normalize_source(source: str | None) -> str | None:
    key = re.sub(r"[^a-z0-9_]+", "", str(source or "").strip().lower())
    return SOURCE_ALIASES.get(key)

def parse_rank(text: str) -> dict:
    m = re.fullmatch(r"\s*Page\s*(\d+)\s*,\s*Pos\s*(\d+)\s*/\s*(\d+)\s*", text or "", re.I)
    if not m:
        return {"raw": text, "valid": False}
    page, position, total = map(int, m.groups())
    if page < 1:
        return {"raw": text, "valid": False, "error": "page_must_be_positive"}
    if total < 1:
        return {"raw": text, "valid": False, "error": "total_must_be_positive"}
    if position < 1 or position > total:
        return {"raw": text, "valid": False, "error": "position_out_of_range"}
    denominator = total - 1
    normalized = 0.0 if denominator == 0 else (position - 1) / denominator
    return {
        "raw": text,
        "valid": True,
        "page": page,
        "position": position,
        "total": total,
        "normalized_position": normalized,
    }


def compare(sources: list[dict]) -> dict:
    valid = [s for s in sources if s.get("valid")]
    invalid = [s for s in sources if not s.get("valid")]
    if invalid:
        return {
            "status": "INVALID_INPUT",
            "message": "One or more rank strings are missing or invalid",
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "invalid_sources": invalid,
        }
    if not valid:
        return {"status": "INVALID_INPUT", "message": "No parseable rank string"}
    raw_labels = [str(s.get("source", "")).strip() for s in valid]
    if any(not label for label in raw_labels):
        return {"status": "INVALID_INPUT", "message": "Every source must have a non-empty source label"}
    normalized_labels = [normalize_source(label) for label in raw_labels]
    if any(label is None for label in normalized_labels):
        return {"status": "INVALID_INPUT", "message": "Unknown source label", "sources": raw_labels}
    if len(set(normalized_labels)) != len(normalized_labels):
        return {"status": "INVALID_INPUT", "message": "Aliases of the same source cannot prove cross-source agreement", "normalized_sources": normalized_labels}
    if len(valid) < 2:
        return {"status": "INSUFFICIENT_SOURCES", "message": "At least two distinct sources are required for comparison", "valid_count": len(valid), "normalized_sources": normalized_labels}
    pages = {s["page"] for s in valid}
    values = [s["normalized_position"] for s in valid]
    spread = max(values) - min(values)
    exact = len({(s["page"], s["position"], s["total"]) for s in valid}) == 1
    return {
        "status": "MATCH" if exact and len(pages) == 1 else "DIFFERENT_SOURCES_DO_NOT_MERGE",
        "same_page": len(pages) == 1,
        "normalized_spread": spread,
        "valid_source_count": len(valid),
        "normalized_sources": normalized_labels,
        "note": "Rank strings come from different interfaces/result sets. Keep source labels and totals; do not average them.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", action="append", required=True, help="label=Page 1, Pos 6/50")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rows = []
    for item in args.source:
        if "=" not in item:
            p.error("--source must be label=rank")
        label, raw = item.split("=", 1)
        row = {"source": label, **parse_rank(raw)}
        rows.append(row)
    result = {"sources": rows, "comparison": compare(rows)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(row)
        print("comparison:", result["comparison"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
