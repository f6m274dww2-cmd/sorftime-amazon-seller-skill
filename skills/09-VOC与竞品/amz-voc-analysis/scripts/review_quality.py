#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit Customers Say counts, deduplicate reviews, and filter a target variant.

Usage:
  python3 scripts/review_quality.py     --customers-say customers_say.json     --reviews reviews_positive.json     --variant "24 oz"     --out-dir ./voc-clean

Inputs accept raw MCP output or the {"data": ...} wrapper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any


def unwrap(payload: Any) -> Any:
    return payload.get("data") if isinstance(payload, dict) and "data" in payload else payload


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_nonnegative_int(value) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return int(value) if math.isfinite(value) and value.is_integer() and value >= 0 else None
    if isinstance(value, str):
        text = value.strip()
        return int(text) if re.fullmatch(r"\d+", text) else None
    return None


def _parse_evidence_date(value: Any) -> date | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            return None
        timestamp = float(value) / 1000 if value > 10_000_000_000 else float(value)
        try:
            return datetime.fromtimestamp(timestamp).date()
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    try:
        if re.fullmatch(r"\d{8}", text):
            return datetime.strptime(text, "%Y%m%d").date()
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def audit_customers_say(payload: Any, as_of: date | None = None, max_age_days: int = 45) -> dict:
    payload = unwrap(payload) or {}
    topics = payload.get("details") or []
    issues = []
    normalized = []
    seen_keywords = set()
    today = as_of or date.today()
    for i, row in enumerate(topics):
        keyword_text = _normal_text(row.get("keyword"))
        mention = parse_nonnegative_int(row.get("mention"))
        positive = parse_nonnegative_int(row.get("positive"))
        negative = parse_nonnegative_int(row.get("negative"))
        if mention is None or positive is None or negative is None:
            issues.append({"index": i, "keyword": row.get("keyword"), "issue": "invalid_nonnegative_integer_counts", "mention": row.get("mention"), "positive": row.get("positive"), "negative": row.get("negative")})
            continue
        row_issues = []
        if not keyword_text:
            row_issues.append("missing_keyword")
        elif keyword_text in seen_keywords:
            row_issues.append("duplicate_keyword")
        else:
            seen_keywords.add(keyword_text)
        update_text = row.get("update_time")
        update_date = _parse_evidence_date(update_text)
        if update_date is None:
            row_issues.append("invalid_update_time")
        else:
            if update_date > today:
                row_issues.append("future_update_time")
            if (today - update_date).days > max_age_days:
                row_issues.append("stale_update_time")
        if mention < 0 or positive < 0 or negative < 0:
            row_issues.append("negative_count")
        if positive > mention:
            row_issues.append("positive_exceeds_mention")
        if negative > mention:
            row_issues.append("negative_exceeds_mention")
        if positive + negative > mention:
            row_issues.append("positive_plus_negative_exceeds_mention")
        if row_issues:
            issues.append({
                "index": i,
                "keyword": row.get("keyword"),
                "mention": mention,
                "positive": positive,
                "negative": negative,
                "issues": row_issues,
            })
        normalized.append({
            "keyword": row.get("keyword"),
            "mention": mention,
            "positive": positive,
            "negative": negative,
            "negative_ratio": (negative / mention) if mention else None,
            "valid": not row_issues,
            "content": row.get("content"),
            "update_time": row.get("update_time"),
            "update_date": update_date.isoformat() if update_date else None,
        })
    return {
        "ready_for_decision": not issues and bool(normalized),
        "issue_count": len(issues),
        "issues": issues,
        "topics": normalized,
        "customer_say": payload.get("customer_say"),
    }


def _field(row: dict, *names: str) -> Any:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return ""


def _field_values(row: dict, *names: str) -> list[str]:
    values = []
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            values.append(str(value).strip())
    return values


def _normal_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _review_metadata(row: dict) -> tuple[tuple[tuple[str, str], ...], dict[str, list[str]]]:
    fields = {
        "rating": ("rating", "star", "stars", "star_rating", "Rating"),
        "date": ("review_date", "date", "review_time", "reviewDate"),
        "verified": ("verified_purchase", "verified", "isVerified"),
        "vine": ("vine", "isVine"),
        "helpful": ("helpful_votes", "helpful", "helpful_count"),
    }

    def normalize_metadata_value(canonical: str, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if canonical == "rating":
            try:
                return f"{float(value):.1f}"
            except (TypeError, ValueError, OverflowError):
                return _normal_text(value)
        if canonical == "date":
            parsed_date = _parse_evidence_date(value)
            return parsed_date.isoformat() if parsed_date else _normal_text(value)
        if canonical in {"verified", "vine"}:
            text = _normal_text(value)
            if text in {"1", "true", "yes", "y"}:
                return "true"
            if text in {"0", "false", "no", "n"}:
                return "false"
            return text
        if canonical == "helpful":
            try:
                return str(int(value))
            except (TypeError, ValueError, OverflowError):
                return _normal_text(value)
        return _normal_text(value)

    metadata = []
    conflicts = {}
    for canonical, aliases in fields.items():
        values = []
        for alias in aliases:
            value = row.get(alias)
            if value not in (None, ""):
                normalized = normalize_metadata_value(canonical, value)
                if normalized and normalized not in values:
                    values.append(normalized)
        if len(values) > 1:
            conflicts[canonical] = values
        if values:
            metadata.append((canonical, values[0]))
    return tuple(metadata), conflicts


SIZE_TOKEN_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*(fl\s*oz|ounces|ounce|oz|milliliters|milliliter|ml|liters|liter|l|lbs|lb|kg|g)(?![a-z])", re.I)
CANONICAL_SIZE_TOKEN_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*(ambiguous-oz|ml|g)(?![a-z])", re.I)
SIZE_REL_TOLERANCE = 0.001


def _canonical_size(amount: str, unit: str, oz_mode: str = "ambiguous") -> str:
    value = float(amount)
    unit = re.sub(r"\s+", "", unit.lower())
    if unit == "floz":
        return f"{value * 29.5735295625:.6f} ml"
    if unit in {"ounce", "ounces", "oz"}:
        if oz_mode == "volume":
            return f"{value * 29.5735295625:.6f} ml"
        if oz_mode == "mass":
            return f"{value * 28.349523125:.6f} g"
        return f"{value:.6f} ambiguous-oz"
    if unit in {"milliliter", "milliliters", "ml"}:
        return f"{value:.6f} ml"
    if unit in {"liter", "liters", "l"}:
        return f"{value * 1000:.6f} ml"
    if unit == "lb" or unit == "lbs":
        return f"{value * 453.59237:.6f} g"
    if unit == "kg":
        return f"{value * 1000:.6f} g"
    if unit == "g":
        return f"{value:.6f} g"
    return f"{value:g} {unit}"


def _normalize_attr_text(value: Any, oz_mode: str = "ambiguous") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    text = re.sub(r"\s*([=:,;|])\s*", r"\1", text)
    return SIZE_TOKEN_RE.sub(lambda m: _canonical_size(m.group(1), m.group(2), oz_mode), text)


def _normalize_review_id(value: Any) -> str:
    """Normalize an opaque review ID without applying product-unit conversions."""
    return str(value or "").strip().lower()


def _quantity_profile(value: Any, oz_mode: str = "ambiguous") -> tuple[str, tuple[tuple[float, str], ...]]:
    """Return a text skeleton plus structured quantities in canonical base units."""
    normalized = _normalize_attr_text(value, oz_mode)
    quantities = tuple(
        (float(amount), re.sub(r"\s+", "", unit.lower()))
        for amount, unit in CANONICAL_SIZE_TOKEN_RE.findall(normalized)
    )
    skeleton = CANONICAL_SIZE_TOKEN_RE.sub("<size>", normalized)
    return skeleton, quantities


def _quantities_equivalent(left: tuple[float, str], right: tuple[float, str]) -> bool:
    left_value, left_unit = left
    right_value, right_unit = right
    if left_unit != right_unit:
        return False
    if not (math.isfinite(left_value) and math.isfinite(right_value)):
        return False
    scale = max(abs(left_value), abs(right_value), 1e-12)
    return abs(left_value - right_value) / scale <= SIZE_REL_TOLERANCE


def _values_equivalent(left: Any, right: Any, oz_mode: str = "ambiguous") -> bool:
    left_skeleton, left_quantities = _quantity_profile(left, oz_mode)
    right_skeleton, right_quantities = _quantity_profile(right, oz_mode)
    if left_skeleton != right_skeleton or len(left_quantities) != len(right_quantities):
        return False
    return all(
        _quantities_equivalent(left_qty, right_qty)
        for left_qty, right_qty in zip(left_quantities, right_quantities)
    )


def _parse_variant_tokens(text: str, oz_mode: str = "ambiguous"):
    raw_attrs: dict[str, list[str]] = {}
    bare = []
    for part in re.split(r"[;|,]", _normalize_attr_text(text, oz_mode)):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
        elif ":" in part and part.count(":") == 1:
            key, value = part.split(":", 1)
        else:
            bare.append(part)
            continue
        raw_attrs.setdefault(_normalize_attr_text(key, oz_mode), []).append(
            _normalize_attr_text(value, oz_mode)
        )
    attrs = {key: values[0] for key, values in raw_attrs.items()}
    conflicts = {
        key: sorted(set(values))
        for key, values in raw_attrs.items()
        if any(not _values_equivalent(values[0], value, oz_mode) for value in values[1:])
    }
    return attrs, sorted(bare), conflicts


def _variants_equivalent(left: str, right: str, oz_mode: str = "ambiguous") -> bool:
    left_attrs, left_bare, left_conflicts = _parse_variant_tokens(left, oz_mode)
    right_attrs, right_bare, right_conflicts = _parse_variant_tokens(right, oz_mode)
    if left_conflicts or right_conflicts or set(left_attrs) != set(right_attrs):
        return False
    if len(left_bare) != len(right_bare):
        return False
    if not all(_values_equivalent(left_attrs[key], right_attrs[key], oz_mode) for key in left_attrs):
        return False
    return all(_values_equivalent(a, b, oz_mode) for a, b in zip(left_bare, right_bare))


def _variant_key(variant: str, stable_id: str | None = None, oz_mode: str = "ambiguous") -> str:
    if stable_id:
        return f"id:{stable_id.strip().lower()}"
    attrs, bare, conflicts = _parse_variant_tokens(variant, oz_mode)
    if conflicts:
        payload = ";".join(f"{k}={'|'.join(v)}" for k, v in sorted(conflicts.items()))
        return f"conflict:{payload}|raw:{_normalize_attr_text(variant, oz_mode)}"
    if attrs:
        return "attrs:" + ";".join(f"{k}={attrs[k]}" for k in sorted(attrs)) + (f"|bare:{','.join(bare)}" if bare else "")
    normalized = _normalize_attr_text(variant, oz_mode)
    return f"text:{normalized}" if normalized else "[unlabeled]"


def _size_tokens(text: str, oz_mode: str = "ambiguous") -> list[str]:
    _, quantities = _quantity_profile(text, oz_mode)
    return [f"{float(amount):g} {unit.lower()}" for amount, unit in quantities]


def _pack_count(text: Any) -> int | None:
    match = re.search(r"(?<!\d)(\d+)\s*pack(?:s)?(?!\w)", str(text or ""), re.I)
    return int(match.group(1)) if match else None


def _trusted_label_matches(label: str, target_property: str, oz_mode: str) -> bool:
    """Compare a sparse review label without requiring optional dimensions."""
    _, target_quantities = _quantity_profile(target_property, oz_mode)
    _, candidate_quantities = _quantity_profile(label, oz_mode)
    if candidate_quantities and target_quantities:
        if not all(any(_quantities_equivalent(candidate, target) for target in target_quantities)
                   for candidate in candidate_quantities):
            return False
    elif candidate_quantities and not target_quantities:
        return False
    target_pack = _pack_count(target_property)
    candidate_pack = _pack_count(label)
    if target_pack is not None and candidate_pack is not None and target_pack != candidate_pack:
        return False
    return True


def _is_target_variant(variant: str, target_variant: str, oz_mode: str = "ambiguous") -> bool:
    target = target_variant.strip()
    if "=" in target:
        target_attrs, _, target_conflicts = _parse_variant_tokens(target, oz_mode)
        candidate_attrs, candidate_bare, candidate_conflicts = _parse_variant_tokens(variant, oz_mode)
        if target_conflicts or candidate_conflicts or not target_attrs or not candidate_attrs:
            return False
        if candidate_bare or set(candidate_attrs) != set(target_attrs):
            return False
        return all(
            key in candidate_attrs and _values_equivalent(candidate_attrs[key], value, oz_mode)
            for key, value in target_attrs.items()
        )
    target_sizes = _size_tokens(target, oz_mode)
    candidate_sizes = _size_tokens(variant, oz_mode)
    if target_sizes:
        if len(candidate_sizes) != 1 or len(target_sizes) != 1:
            return False
        candidate_attrs, candidate_bare, candidate_conflicts = _parse_variant_tokens(variant, oz_mode)
        if candidate_conflicts:
            return False
        candidate_components = list(candidate_attrs.values()) + candidate_bare
        for component in candidate_components:
            skeleton, quantities = _quantity_profile(component, oz_mode)
            leftover = re.sub(r"[^a-z0-9]+", "", skeleton.replace("<size>", ""))
            if len(quantities) != 1 or leftover:
                return False
        try:
            ta, tu = target_sizes[0].split()
            ca, cu = candidate_sizes[0].split()
            return _quantities_equivalent((float(ta), tu), (float(ca), cu))
        except (ValueError, TypeError):
            return False
    return _variants_equivalent(variant, target, oz_mode)


def clean_reviews(
    payload: Any,
    target_variant: str | None = None,
    oz_mode: str = "ambiguous",
    expected_target_child_asin: str | None = None,
    trusted_child_identity: bool = False,
    trusted_target_property: str | None = None,
    trusted_variation_properties: dict[str, str] | None = None,
) -> tuple[list[dict], dict]:
    rows = unwrap(payload) or []
    if not isinstance(rows, list):
        raise ValueError("reviews payload must be a list or {'data': list}")
    if oz_mode not in {"ambiguous", "volume", "mass"}:
        raise ValueError("oz_mode must be one of: ambiguous, volume, mass")
    expected_target_child = (
        expected_target_child_asin.strip().lower() if expected_target_child_asin else None
    )
    variation_properties = {
        str(asin).strip().lower(): str(prop)
        for asin, prop in (trusted_variation_properties or {}).items()
    }

    records = []
    inconsistent_child_labels = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"reviews payload row {idx} must be an object")
        title = _normal_text(_field(row, "title", "Title"))
        content = _normal_text(_field(row, "content", "Content"))
        variant_values = _field_values(row, "variant_attribute", "AsinProperty", "asin_property")
        stable_values = [v.lower() for v in _field_values(row, "variant_asin", "child_asin", "variation_id")]
        stable_ids = set(stable_values)
        id_conflict = len(stable_ids) > 1
        stable_id = next(iter(stable_ids)) if len(stable_ids) == 1 and not id_conflict else None
        if (
            trusted_child_identity
            and stable_id
            and variant_values
            and stable_id in variation_properties
            and any(
                not _trusted_label_matches(label, variation_properties[stable_id], oz_mode)
                for label in variant_values
            )
        ):
            inconsistent_child_labels.append({
                "original_index": idx,
                "variant_asin": stable_id,
                "variant_attribute": variant_values[0],
                "trusted_property": variation_properties[stable_id],
                "quality_flag": "INCONSISTENT_CHILD_VARIANT_LABEL",
            })
            continue
        label_conflict = any(
            not _variants_equivalent(left, right, oz_mode)
            for i, left in enumerate(variant_values)
            for right in variant_values[i + 1:]
        )
        signature = _variant_key(variant_values[0], oz_mode=oz_mode) if variant_values and not label_conflict else (
            "[unlabeled]" if not variant_values else f"conflict:{idx}"
        )
        review_ids = {
            normalized
            for normalized in (
                _normalize_review_id(value)
                for value in _field_values(row, "review_id", "reviewId")
            )
            if normalized
        }
        review_id_conflict = len(review_ids) > 1
        metadata_signature, metadata_conflicts = _review_metadata(row)
        insufficient_content = not title and not content
        metadata_conflict = bool(metadata_conflicts)
        variant_record_conflict = id_conflict or label_conflict
        record_ambiguous = variant_record_conflict or review_id_conflict or metadata_conflict
        records.append({
            "record": dict(row), "original_index": idx, "variant": variant_values[0] if variant_values else "",
            "variant_values": variant_values, "variant_signature": signature, "stable_id": stable_id,
            "metadata_signature": metadata_signature, "metadata_conflicts": metadata_conflicts,
            "id_conflict": id_conflict, "label_conflict": label_conflict,
            "variant_record_conflict": variant_record_conflict,
            "review_ids": review_ids, "review_id_conflict": review_id_conflict,
            "review_metadata_conflict": metadata_conflict,
            "record_ambiguous": record_ambiguous,
            "insufficient_content": insufficient_content,
            "title": title, "content": content,
        })

    def labels_compatible(group: list[dict]) -> bool:
        """Use complete-link compatibility; fuzzy equality is not transitive."""
        labels = [label for rec in group for label in rec["variant_values"]]
        return all(
            _variants_equivalent(left, right, oz_mode)
            for index, left in enumerate(labels)
            for right in labels[index + 1:]
        )

    stable_groups: dict[str, list[dict]] = {}
    for rec in records:
        if rec["stable_id"]:
            stable_groups.setdefault(rec["stable_id"], []).append(rec)

    conflicting_stable_ids = set()
    for stable_id, group in stable_groups.items():
        if not trusted_child_identity and not labels_compatible(group):
            conflicting_stable_ids.add(stable_id)
            for rec in group:
                rec["ambiguous_identity"] = True
                rec["stable_identity_conflict"] = True

    # Build a stable identity per record. Missing IDs bridge only when their
    # complete label set resolves to exactly one real stable ID.
    bridged = 0
    for rec in records:
        if rec["record_ambiguous"]:
            rec["identity"] = f"ambiguous-record:{rec['original_index']}"
            rec["ambiguous_identity"] = True
        elif rec["stable_id"]:
            rec["identity"] = f"id:{rec['stable_id']}"
            rec.setdefault("ambiguous_identity", False)
        else:
            ids = {
                stable_id
                for stable_id, group in stable_groups.items()
                if stable_id not in conflicting_stable_ids
                and any(candidate["variant_values"] for candidate in group)
                and rec["variant_values"]
                and labels_compatible([rec, *group])
            }
            if len(ids) == 1:
                rec["identity"] = f"id:{next(iter(ids))}"
                rec["ambiguous_identity"] = False
                bridged += 1
            elif len(ids) > 1:
                rec["identity"] = f"ambiguous:{rec['variant_signature']}:{rec['original_index']}"
                rec["ambiguous_identity"] = True
            else:
                rec["identity"] = rec["variant_signature"]
                rec["ambiguous_identity"] = False

    # A review ID is a global review identity, not a variant-local dedupe key.
    # If one ID is attached to incompatible variants or stable ASINs, block the
    # entire group so no arbitrary row can survive as the "right" copy.
    review_groups: dict[str, list[dict]] = {}
    for rec in records:
        for review_id in rec["review_ids"]:
            review_groups.setdefault(review_id, []).append(rec)

    for review_id, group in review_groups.items():
        stable_ids = {rec["stable_id"] for rec in group if rec["stable_id"]}
        variant_conflict = (
            len(stable_ids) > 1
            or (not trusted_child_identity and not labels_compatible(group))
            or any(rec["variant_record_conflict"] or rec["review_id_conflict"] for rec in group)
        )
        content_versions = {
            (rec["title"], rec["content"])
            for rec in group
            if not rec["insufficient_content"]
        }
        metadata_versions = {
            rec["metadata_signature"] for rec in group if rec["metadata_signature"]
        }
        content_conflict = len(content_versions) > 1
        metadata_conflict = len(metadata_versions) > 1 or any(
            rec["review_metadata_conflict"] for rec in group
        )
        if variant_conflict or content_conflict or metadata_conflict:
            for rec in group:
                rec["ambiguous_identity"] = True
                if variant_conflict:
                    rec["review_identity_conflict"] = True
                if content_conflict:
                    rec["review_content_conflict"] = True
                if metadata_conflict:
                    rec["review_metadata_conflict"] = True
        else:
            for rec in group:
                rec["resolved_review_id"] = review_id

    # Resolve target ownership at review-ID level so an unlabeled duplicate
    # inherits the group's variant regardless of input order.
    review_labels = {
        review_id: [label for rec in group for label in rec["variant_values"]]
        for review_id, group in review_groups.items()
    }
    identity_labels: dict[str, list[str]] = {}
    for rec in records:
        if rec["variant"]:
            identity_labels.setdefault(rec["identity"], []).append(rec["variant"])

    def target_ownership(labels: list[str], stable_ids: set[str]) -> str:
        if expected_target_child:
            if not stable_ids or any(stable_id != expected_target_child for stable_id in stable_ids):
                return "other" if stable_ids else "unlabeled"
            if not target_variant:
                return "conflict"
            if trusted_child_identity:
                if not labels:
                    return "target"
                return "target" if all(
                    _trusted_label_matches(label, trusted_target_property or target_variant, oz_mode)
                    for label in labels
                ) else "conflict"
            if not labels:
                return "unlabeled"
            matches = [_is_target_variant(label, target_variant, oz_mode) for label in labels] if target_variant else []
            return "target" if all(matches) else "conflict"
        if not labels:
            return "unlabeled"
        if not target_variant:
            return "other"
        matches = [_is_target_variant(label, target_variant, oz_mode) for label in labels]
        if all(matches):
            return "target"
        if not any(matches):
            return "other"
        return "conflict"

    review_target_states = {
        review_id: target_ownership(
            labels,
            {rec["stable_id"] for rec in review_groups[review_id] if rec["stable_id"]},
        )
        for review_id, labels in review_labels.items()
    }
    identity_target_states = {
        identity: target_ownership(
            labels,
            {identity.removeprefix("id:")} if identity.startswith("id:") else set(),
        )
        for identity, labels in identity_labels.items()
    }
    for review_id, group in review_groups.items():
        if review_target_states[review_id] == "conflict" and not any(
            group_member.get("review_identity_conflict") for group_member in group
        ):
            for group_member in group:
                group_member["ambiguous_identity"] = True
                group_member["target_ownership_conflict"] = True
    for identity, state in identity_target_states.items():
        if state == "conflict":
            for group_member in records:
                if group_member["identity"] == identity:
                    if trusted_child_identity and group_member["review_ids"]:
                        continue
                    group_member["ambiguous_identity"] = True
                    group_member["target_ownership_conflict"] = True

    for rec in records:
        if rec["ambiguous_identity"]:
            rec["group"] = "ambiguous"
        else:
            review_id = next(iter(rec["review_ids"])) if len(rec["review_ids"]) == 1 else None
            labels = review_labels.get(review_id, []) if review_id else identity_labels.get(rec["identity"], [])
            rec["group"] = review_target_states[review_id] if review_id else identity_target_states.get(rec["identity"], "unlabeled")

    # Content-only candidates must also agree on decision-relevant metadata.
    # A missing value is allowed, but two different non-empty values are not.
    content_candidates: dict[tuple[str, str], list[dict]] = {}
    for rec in records:
        if rec["ambiguous_identity"] or rec["review_ids"] or rec["insufficient_content"]:
            continue
        key = (rec["title"], rec["content"])
        content_candidates.setdefault(key, []).append(rec)

    def content_variants_compatible(left: dict, right: dict) -> bool:
        stable_ids = {value for value in [left["stable_id"], right["stable_id"]] if value}
        if len(stable_ids) > 1:
            return False
        return labels_compatible([left, right])

    for content_index, candidates in enumerate(content_candidates.values()):
        clusters: list[list[dict]] = []
        ordered = sorted(
            candidates,
            key=lambda rec: (
                0 if rec["variant_values"] else 1,
                0 if rec["stable_id"] else 1,
                rec["stable_id"] or "",
                rec["variant_signature"],
                rec["original_index"],
            ),
        )
        for rec in ordered:
            matches = [
                cluster for cluster in clusters
                if all(content_variants_compatible(rec, member) for member in cluster)
            ]
            if len(matches) == 1:
                matches[0].append(rec)
            elif len(matches) > 1:
                rec["ambiguous_identity"] = True
                rec["group"] = "ambiguous"
            else:
                clusters.append([rec])

        for cluster_index, cluster in enumerate(clusters):
            dedupe_key = f"content-cluster:{content_index}:{cluster_index}"
            for member in cluster:
                member["content_dedupe_key"] = dedupe_key
            metadata_versions = {
                member["metadata_signature"] for member in cluster if member["metadata_signature"]
            }
            if len(metadata_versions) > 1 or any(member["review_metadata_conflict"] for member in cluster):
                for member in cluster:
                    member["ambiguous_identity"] = True
                    member["review_metadata_conflict"] = True
                    member["group"] = "ambiguous"

    # Every non-ambiguous review ID has exactly one deterministic representative.
    # Prefer usable content and the most complete variant identity, then input order.
    review_representatives: dict[str, int] = {}
    for review_id, group in review_groups.items():
        if any(rec["ambiguous_identity"] for rec in group):
            continue
        representative = min(
            group,
            key=lambda rec: (
                0 if not rec["insufficient_content"] else 1,
                0 if rec["stable_id"] else 1,
                0 if rec["variant_values"] else 1,
                0 if rec["metadata_signature"] else 1,
                rec["original_index"],
            ),
        )
        review_representatives[review_id] = representative["original_index"]

    kept, duplicates = [], []
    seen_by_identity: dict[str, dict[str, int]] = {}
    for rec in records:
        output = dict(rec["record"])
        output["original_index"] = rec["original_index"]
        if rec["ambiguous_identity"]:
            if rec.get("review_content_conflict"):
                output["quality_flag"] = "REVIEW_CONTENT_CONFLICT"
            elif rec.get("review_metadata_conflict"):
                output["quality_flag"] = "REVIEW_METADATA_CONFLICT"
            elif rec.get("stable_identity_conflict") or rec.get("review_identity_conflict"):
                output["quality_flag"] = "AMBIGUOUS_VARIANT"
            elif rec.get("target_ownership_conflict"):
                output["quality_flag"] = "TARGET_OWNERSHIP_CONFLICT"
            else:
                output["quality_flag"] = "AMBIGUOUS_VARIANT"
            output["insufficient_content"] = rec["insufficient_content"]
            kept.append(output)
            continue
        review_id = next(iter(rec["review_ids"])) if len(rec["review_ids"]) == 1 else None
        if review_id:
            representative_index = review_representatives[review_id]
            if rec["original_index"] != representative_index:
                duplicates.append({
                    "index": rec["original_index"],
                    "duplicate_of": representative_index,
                    "variant": rec["variant"],
                    "title": rec["title"][:120],
                    "insufficient_content": rec["insufficient_content"],
                    "reason": "review_id_global_duplicate",
                })
                continue
        if rec["insufficient_content"]:
            output["quality_flag"] = "INSUFFICIENT_CONTENT"
            kept.append(output)
            continue
        signature_text = f"{rec['title']}|{rec['content']}"
        signature = hashlib.sha256(signature_text.encode("utf-8")).hexdigest()
        # Content-only dedupe remains within the exact label identity. Unit
        # equivalence is used for conflict detection and ID bridging, not as
        # permission to merge otherwise unlabeled review rows by content alone.
        dedupe_identity = rec.get("content_dedupe_key") or f"{rec['identity']}|{rec['variant_signature']}"
        seen = seen_by_identity.setdefault(dedupe_identity, {})
        if signature in seen:
            duplicates.append({
                "index": rec["original_index"], "duplicate_of": seen[signature],
                "variant": rec["variant"], "title": rec["title"][:120],
            })
            continue
        seen[signature] = rec["original_index"]
        kept.append(output)

    group_map = {m["original_index"]: m["group"] for m in records}
    target_rows = [r for r in kept if group_map.get(r["original_index"]) == "target"]
    other_rows = [r for r in kept if group_map.get(r["original_index"]) == "other"]
    unlabeled_rows = [r for r in kept if group_map.get(r["original_index"]) == "unlabeled"]
    insufficient = [r for r in kept if r.get("quality_flag") == "INSUFFICIENT_CONTENT"]
    ambiguous_records = [r for r in kept if r.get("quality_flag") == "AMBIGUOUS_VARIANT"]
    review_content_conflict_records = [
        r for r in kept if r.get("quality_flag") == "REVIEW_CONTENT_CONFLICT"
    ]
    review_metadata_conflict_records = [
        r for r in kept if r.get("quality_flag") == "REVIEW_METADATA_CONFLICT"
    ]
    target_ownership_conflict_records = [
        r for r in kept if r.get("quality_flag") == "TARGET_OWNERSHIP_CONFLICT"
    ]
    ambiguous_rows = ambiguous_records
    ambiguous_with_insufficient = [r for r in ambiguous_records if r.get("insufficient_content")]
    blocked_flags = {
        "INSUFFICIENT_CONTENT",
        "AMBIGUOUS_VARIANT",
        "REVIEW_CONTENT_CONFLICT",
        "REVIEW_METADATA_CONFLICT",
        "TARGET_OWNERSHIP_CONFLICT",
    }
    review_content_conflict_rows = len(review_content_conflict_records)
    review_metadata_conflict_rows = len(review_metadata_conflict_records)
    target_ownership_conflict_rows = len(target_ownership_conflict_records)
    usable = [r for r in kept if r.get("quality_flag") not in blocked_flags]
    selected = target_rows if target_variant else kept
    accounted_rows = (
        len(usable)
        + len(duplicates)
        + len(insufficient)
        + len(ambiguous_records)
        + review_content_conflict_rows
        + review_metadata_conflict_rows
        + target_ownership_conflict_rows
        + len(inconsistent_child_labels)
    )
    target_stable_ids = {
        record["stable_id"]
        for record in records
        if group_map.get(record["original_index"]) == "target" and record["stable_id"]
    }
    if not expected_target_child:
        target_identity_status = "VARIANT_LABEL_ONLY" if target_rows else "UNRESOLVED"
    elif target_rows and target_stable_ids == {expected_target_child}:
        target_identity_status = "RESOLVED_STABLE_ID"
    else:
        target_identity_status = "UNRESOLVED"
    dimension_text = trusted_target_property or target_variant
    if dimension_text and "=" in dimension_text:
        target_attrs, target_bare, target_conflicts = _parse_variant_tokens(dimension_text, oz_mode)
        target_dimensions = {
            "attrs": target_attrs,
            "bare": target_bare,
            "quantities": [],
            "conflicts": target_conflicts,
        }
    else:
        target_dimensions = {
            "attrs": {},
            "bare": [_normalize_attr_text(dimension_text, oz_mode)] if dimension_text else [],
            "quantities": [
                {"value": value, "unit": unit}
                for value, unit in _quantity_profile(dimension_text, oz_mode)[1]
            ] if dimension_text else [],
            "conflicts": {},
        }
    target_record_indexes = {
        record["original_index"] for record in records
        if group_map.get(record["original_index"]) == "target"
    }
    target_dimension_bindings = [
        {
            "original_index": record["original_index"],
            "stable_id": record["stable_id"],
            "variant_label": record["variant"],
            "matches_target": (
                _trusted_label_matches(record["variant"], trusted_target_property or target_variant, oz_mode)
                if trusted_child_identity else _is_target_variant(record["variant"], target_variant, oz_mode)
            ) if target_variant else False,
        }
        for record in records
        if record["original_index"] in target_record_indexes
    ]
    target_dimension_status = (
        "RESOLVED"
        if target_dimension_bindings
        and all(
            binding["stable_id"] == expected_target_child
            and binding["matches_target"]
            for binding in target_dimension_bindings
        )
        else "UNRESOLVED"
    )

    report = {
        "input_rows": len(rows),
        "deduped_rows": len(usable),
        "duplicates_removed": len(duplicates),
        "duplicate_insufficient_content_rows": sum(
            1 for item in duplicates if item.get("insufficient_content")
        ),
        "duplicate_details": duplicates,
        "target_variant": target_variant,
        "target_oz_mode": oz_mode,
        "trusted_child_identity": trusted_child_identity,
        "trusted_target_property": trusted_target_property,
        "target_child_asin": expected_target_child_asin.strip() if expected_target_child_asin else None,
        "target_identity_status": target_identity_status,
        "target_dimensions": target_dimensions,
        "target_dimension_status": target_dimension_status,
        "target_dimension_bindings": target_dimension_bindings,
        "target_variant_rows": sum(1 for r in target_rows if r.get("quality_flag") not in blocked_flags),
        "target_variant_total_rows": len(target_rows),
        "target_variant_insufficient_rows": sum(1 for r in target_rows if r.get("quality_flag") == "INSUFFICIENT_CONTENT"),
        "other_variant_rows": sum(1 for r in other_rows if r.get("quality_flag") not in blocked_flags),
        "other_variant_total_rows": len(other_rows),
        "unlabeled_variant_rows": sum(1 for r in unlabeled_rows if r.get("quality_flag") not in blocked_flags),
        "unlabeled_variant_total_rows": len(unlabeled_rows),
        "insufficient_content_rows": len(insufficient),
        "insufficient_content_details": [
            {"original_index": r.get("original_index"), "variant": _field(r, "variant_attribute", "AsinProperty", "asin_property"), "quality_flag": "INSUFFICIENT_CONTENT"}
            for r in insufficient
        ],
        "insufficient_content_records": insufficient,
        "ambiguous_variant_rows": len(ambiguous_rows),
        "ambiguous_with_insufficient_content_rows": len(ambiguous_with_insufficient),
        "ambiguous_variant_records": ambiguous_rows,
        "review_content_conflict_rows": review_content_conflict_rows,
        "review_content_conflict_records": review_content_conflict_records,
        "review_metadata_conflict_rows": review_metadata_conflict_rows,
        "review_metadata_conflict_records": review_metadata_conflict_records,
        "target_ownership_conflict_rows": target_ownership_conflict_rows,
        "target_ownership_conflict_records": target_ownership_conflict_records,
        "inconsistent_child_label_rows": len(inconsistent_child_labels),
        "inconsistent_child_label_records": inconsistent_child_labels,
        "bridged_variant_id_rows": bridged,
        "review_identity_group_count": len(review_groups),
        "review_identity_conflict_rows": sum(
            1 for rec in records if rec.get("review_identity_conflict")
        ),
        "variant_counts": dict(Counter(
            str(_field(r, "variant_attribute", "AsinProperty", "asin_property")).strip() or "[unlabeled]"
            for r in kept
        )),
        "returned_rows": len(selected),
        "returned_usable_rows": sum(
            1 for row in selected
            if row.get("quality_flag") not in blocked_flags
        ),
        "accounted_rows": accounted_rows,
        "accounting_consistent": accounted_rows == len(rows),
    }
    return selected, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers-say", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--variant", help="Target variant substring, e.g. 24 oz")
    parser.add_argument(
        "--oz-mode",
        choices=["ambiguous", "volume", "mass"],
        default="ambiguous",
        help="How to interpret plain oz; use volume only when the product dimension is confirmed",
    )
    parser.add_argument("--target-child-asin", help="Expected child ASIN / variation ID for target reviews")
    parser.add_argument(
        "--trusted-child-identity",
        action="store_true",
        help="Use a ProductVariations-confirmed child ASIN as authoritative review identity",
    )
    parser.add_argument(
        "--trusted-target-property",
        help="Authoritative ProductVariations Property for the expected child ASIN",
    )
    parser.add_argument("--out-dir", type=Path, default=Path("./voc-clean"))
    args = parser.parse_args()

    if not args.customers_say and not args.reviews:
        parser.error("provide --customers-say and/or --reviews")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    if args.customers_say:
        audit = audit_customers_say(load_json(args.customers_say))
        (args.out_dir / "customers_say_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary["customers_say"] = {
            "ready_for_decision": audit["ready_for_decision"],
            "issue_count": audit["issue_count"],
        }
    if args.reviews:
        cleaned, report = clean_reviews(
            load_json(args.reviews),
            args.variant,
            args.oz_mode,
            args.target_child_asin,
            args.trusted_child_identity,
            args.trusted_target_property,
        )
        (args.out_dir / "reviews_clean.json").write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (args.out_dir / "reviews_quality.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary["reviews"] = report
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
