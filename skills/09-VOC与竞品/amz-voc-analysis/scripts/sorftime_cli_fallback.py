#!/usr/bin/env python3
"""Small, dependency-free fallback for Sorftime CLI review/variation data.

The MCP review schema is intentionally small and can omit child ASINs.  This
adapter calls the official Sorftime CLI and normalizes its PascalCase response
into the shape consumed by review_quality.py.  It never prints the account
key; the CLI keeps credentials in its own profile store.
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
from datetime import datetime
from typing import Any


def _run_cli(endpoint: str, params: dict[str, Any], domain: int = 1) -> dict:
    command = ["sorftime", "api", endpoint, json.dumps(params, ensure_ascii=False), "--domain", str(domain)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "sorftime CLI failed"
        raise RuntimeError(message[:500])
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("sorftime CLI returned non-JSON output") from exc
    code = payload.get("Code", payload.get("code"))
    if code != 0:
        raise RuntimeError(f"sorftime API error Code={code}: {payload.get('Message') or payload.get('message')}")
    return payload


def _parse_variant_property(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value.strip()
    else:
        parsed = value
    if isinstance(parsed, list):
        parts = []
        for item in parsed:
            if isinstance(item, dict):
                name = item.get("name") or item.get("Name") or "Variant"
                detail = item.get("detail") or item.get("Detail") or ""
                parts.append(f"{name}={detail}")
        return "; ".join(parts)
    return str(value or "").strip()


def normalize_reviews(payload: dict) -> list[dict]:
    rows = payload.get("Data") or payload.get("data") or []
    if not isinstance(rows, list):
        raise ValueError("ProductReviewsQuery Data must be a list")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append({
            "review_id": row.get("ReviewId") or row.get("ReviewID") or row.get("reviewId"),
            "reviewId": row.get("ReviewId") or row.get("ReviewID") or row.get("reviewId"),
            "variant_asin": row.get("Asin") or row.get("ASIN") or row.get("asin"),
            "variant_attribute": _parse_variant_property(row.get("AsinProperty") or row.get("AsinProperties")),
            "title": row.get("Title") or row.get("title") or "",
            "content": row.get("Content") or row.get("content") or "",
            "review_date": row.get("ReviewsDate") or row.get("ReviewDate") or row.get("review_date"),
            "star_rating": row.get("Star") or row.get("StarRating") or row.get("star_rating"),
            "verified_purchase": row.get("IsVP") if "IsVP" in row else row.get("verified_purchase"),
            "helpful_votes": row.get("Helpful") if "Helpful" in row else row.get("helpful_votes"),
            "review_link": row.get("ReviewsLink") or row.get("review_link"),
            "update_time": row.get("UpdateTime") or row.get("update_time"),
            "consumer_badge": row.get("ConsumerBadge"),
        })
    return normalized


def normalize_variations(payload: dict) -> list[dict]:
    rows = payload.get("Data") or payload.get("data") or []
    if not isinstance(rows, list):
        raise ValueError("ProductVariations Data must be a list")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append({
            "asin": row.get("Asin") or row.get("ASIN") or row.get("asin"),
            "property": row.get("Property") or row.get("property") or "",
            "sales_amount": row.get("SalesAmount"),
            "item_index": row.get("ItemIndex"),
            "item_total": row.get("ItemTotal"),
        })
    return normalized


def collect_review_data(asin: str, *, domain: int = 1, page: int = 1) -> dict:
    reviews_payload = _run_cli(
        "ProductReviewsQuery",
        {"asin": asin, "pageIndex": page},
        domain=domain,
    )
    variations_payload = _run_cli(
        "ProductVariations",
        {"asin": asin, "pageIndex": 1},
        domain=domain,
    )
    return {
        "asin": asin,
        "reviews": normalize_reviews(reviews_payload),
        "variations": normalize_variations(variations_payload),
        "evidence": {
            "observed_at": datetime.now().isoformat(timespec="seconds"),
            "reviews_response_sha256": hashlib.sha256(
                json.dumps(reviews_payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            "variations_response_sha256": hashlib.sha256(
                json.dumps(variations_payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
        },
        "reviews_code": reviews_payload.get("Code", reviews_payload.get("code")),
        "variations_code": variations_payload.get("Code", variations_payload.get("code")),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch normalized Sorftime review/variation evidence via CLI")
    parser.add_argument("asin")
    parser.add_argument("--domain", type=int, default=1)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--out")
    args = parser.parse_args()
    result = collect_review_data(args.asin, domain=args.domain, page=args.page)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        from pathlib import Path
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
