#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazon P&L calculator with explicit data-quality semantics.

Key rule:
  Sorftime product_detail.profit (legacy gross_profit) is normally:
      price - FBA fee - referral/platform fee
  It is NOT profit after landed cost, ads, returns, storage or fixed costs.

When real FBA fee is missing, the formula estimate is explicitly marked and
the result is blocked from producing a precise Go/No-Go.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import numbers
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def estimate_fba_fee(weight_kg: float) -> float:
    """Rough planning estimate only. Prefer ProductRequest.FbaFee."""
    return max(3.5, weight_kg * 2.5 + 1.5)


SOURCE_RULES = {
    "price": {
        "verified": {"verified", "product_detail", "user_verified"},
        "estimated": {"estimated", "user_estimate", "assumed"},
    },
    "fba": {
        "verified": {"verified", "product_detail", "user_verified"},
        "estimated": {"estimated", "estimated_formula", "user_estimate", "assumed"},
    },
    "platform_fee": {
        "verified": {"verified", "product_detail", "user_verified"},
        "estimated": {"estimated", "estimated_rate", "user_estimate", "assumed"},
    },
    "landed_cost": {
        "verified": {"verified", "supplier_confirmed", "user_verified"},
        "estimated": {"estimated", "user_estimate", "assumed"},
    },
    "monthly_sales": {
        "verified": {"verified", "product_detail", "user_verified"},
        "estimated": {"estimated", "user_estimate", "assumed"},
    },
    "ad_rate": {
        "verified": {"verified", "user_verified"},
        "estimated": {"estimated_rate", "estimated", "assumed", "user_estimate", "default_assumed"},
    },
    "return_rate": {
        "verified": {"verified", "user_verified"},
        "estimated": {"estimated", "assumed", "user_estimate", "default_assumed"},
    },
    "return_processing_fee": {
        "verified": {"verified", "user_verified"},
        "estimated": {"estimated", "assumed", "user_estimate", "default_assumed"},
    },
    "fixed_monthly": {
        "verified": {"verified", "user_verified", "actual"},
        "estimated": {"estimated", "assumed", "user_estimate", "default_assumed"},
    },
    "weight": {
        "verified": {"verified", "product_detail", "user_verified"},
        "estimated": {"estimated", "user_estimate", "assumed"},
    },
    "referral_rate": {
        "verified": {"verified", "product_detail", "user_verified"},
        "estimated": {"estimated_rate", "estimated", "assumed", "user_estimate"},
    },
    "sorftime_profit": {
        "verified": {"verified", "product_detail", "user_verified"},
        "estimated": {"estimated", "user_estimate"},
    },
}


def _source_status(source: str | None, provided: bool, field: str) -> str:
    if not provided:
        return "MISSING"
    value = (source or "USER_INPUT_UNVERIFIED").strip().lower()
    rules = SOURCE_RULES[field]
    if value in rules["verified"]:
        return "VERIFIED"
    if value in rules["estimated"]:
        return "ESTIMATED"
    return "UNVERIFIED"


def _detail_number(detail: dict, field: str, *aliases: str, required: bool = True):
    values = []
    names = tuple(dict.fromkeys((field, *aliases)))
    for name in names:
        if name not in detail:
            continue
        value = detail[name]
        if value is None or value == "":
            continue
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError(
                f"product_detail.{name} must be a numeric value, got {type(value).__name__}"
            )
        try:
            numeric = float(value)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"product_detail.{name} cannot be converted to a finite number") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"product_detail.{name} must be finite")
        values.append((name, numeric))
    if not values:
        if required:
            raise ValueError(f"product_detail.{field} is required")
        return None
    baseline_name, baseline = values[0]
    conflicts = [
        name
        for name, numeric in values[1:]
        if not math.isclose(numeric, baseline, rel_tol=1e-12, abs_tol=1e-9)
    ]
    if conflicts:
        raise ValueError(
            f"product_detail aliases disagree for {field}: "
            f"{baseline_name}={baseline}, " + ", ".join(f"{name}={dict(values)[name]}" for name in conflicts)
        )
    return baseline


def _detail_raw(detail: dict, *names: str):
    for name in names:
        value = detail.get(name)
        if value is not None and value != "":
            return name, value
    return None, None


def compute_from_product_detail(
    product_detail: dict,
    *,
    landed_cost: float,
    source_evidence_overrides: dict[str, dict] | None = None,
    source_response_hash: str | None = None,
    source_observed_at: str | None = None,
    price_source: str | None = "product_detail",
    fba_source: str | None = "product_detail",
    platform_source: str | None = "product_detail",
    monthly_sales_source: str | None = "product_detail",
    sorftime_profit_source: str | None = "product_detail",
    weight_source: str | None = "product_detail",
    **compute_kwargs,
) -> dict:
    """Validate raw Sorftime product_detail fields before any unit conversion."""
    if not isinstance(product_detail, dict):
        raise ValueError("product_detail must be an object")

    price = _detail_number(product_detail, "price")
    fba_fee = _detail_number(product_detail, "fba_fee", "FbaFee")
    platform_fee = _detail_number(product_detail, "platform_fee", "PlatformFee")
    monthly_sales = _detail_number(
        product_detail, "monthly_sales_volume", "MonthlySalesVolume", required=False
    )
    sorftime_profit = _detail_number(product_detail, "profit", "gross_profit", "GrossProfit")
    weight_g = _detail_number(product_detail, "weight_g", "WeightG")
    if weight_g <= 0:
        raise ValueError("product_detail.weight_g must be > 0")

    as_of = compute_kwargs.get("as_of")
    upstream_observed_at = source_observed_at or as_of
    response_hash = source_response_hash or hashlib.sha256(
        json.dumps(product_detail, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    asin = product_detail.get("asin")

    def upstream_evidence(logical_name: str, normalized_value: float, unit: str, *raw_names: str) -> dict:
        raw_field, raw_value = _detail_raw(product_detail, *raw_names)
        return {
            "source": "product_detail",
            "evidence_type": "upstream_response",
            "asin": asin,
            "raw_field": raw_field,
            "raw_value": raw_value,
            "normalized_value": normalized_value,
            "unit": unit,
            "currency": "USD" if unit.startswith("USD") else None,
            "observed_at": upstream_observed_at,
            "response_sha256": response_hash,
        }

    def assumption_evidence(source_name: str, value: float, unit: str) -> dict:
        return {
            "source": compute_kwargs.get(source_name) or "estimated",
            "evidence_type": "assumption",
            "normalized_value": float(value),
            "unit": unit,
            "currency": "USD" if unit.startswith("USD") else None,
            "observed_at": as_of,
        }

    ad_rate = compute_kwargs.get("ad_rate", 0.15)
    return_rate = compute_kwargs.get("return_rate", 0.05)
    return_processing_fee = compute_kwargs.get("return_processing_fee", 3.5)
    fixed_monthly = compute_kwargs.get("fixed_monthly", 500.0)
    source_evidence = {
        "price": upstream_evidence("price", price, "USD/unit", "price"),
        "fba": upstream_evidence("fba", fba_fee, "USD/unit", "fba_fee", "FbaFee"),
        "platform_fee": upstream_evidence("platform_fee", platform_fee, "USD/unit", "platform_fee", "PlatformFee"),
        "monthly_sales": upstream_evidence(
            "monthly_sales", monthly_sales, "units/month", "monthly_sales_volume", "MonthlySalesVolume"
        ) if monthly_sales is not None else None,
        "sorftime_profit": upstream_evidence("sorftime_profit", sorftime_profit, "USD/unit", "profit", "gross_profit", "GrossProfit"),
        "weight": upstream_evidence("weight", weight_g / 1000, "kg", "weight_g", "WeightG"),
        "landed_cost": assumption_evidence("landed_cost_source", landed_cost, "USD/unit"),
        "ad_rate": assumption_evidence("ad_rate_source", ad_rate, "ratio"),
        "return_rate": assumption_evidence("return_rate_source", return_rate, "ratio"),
        "return_processing_fee": assumption_evidence(
            "return_processing_fee_source", return_processing_fee, "USD/unit"
        ),
        "fixed_monthly": assumption_evidence("fixed_monthly_source", fixed_monthly, "USD/month"),
        "referral_rate": assumption_evidence("referral_rate_source", compute_kwargs.get("referral_rate", 0.15), "ratio"),
    }
    source_evidence.update(source_evidence_overrides or {})
    source_evidence = {name: evidence for name, evidence in source_evidence.items() if evidence is not None}

    return compute(
        price=price,
        landed_cost=landed_cost,
        weight_kg=weight_g / 1000,
        fba_fee=fba_fee,
        platform_fee=platform_fee,
        monthly_sales=monthly_sales,
        sorftime_profit=sorftime_profit,
        price_source=price_source,
        fba_source=fba_source,
        platform_source=platform_source,
        monthly_sales_source=monthly_sales_source,
        sorftime_profit_source=sorftime_profit_source,
        weight_source=weight_source,
        source_evidence=source_evidence,
        **compute_kwargs,
    )


def compute(
    *,
    price: float,
    landed_cost: float,
    weight_kg: float,
    referral_rate: float = 0.15,
    platform_fee: float | None = None,
    ad_rate: float | None = None,
    return_rate: float | None = None,
    return_processing_fee: float | None = None,
    fixed_monthly: float | None = None,
    monthly_sales: float | None = None,
    fba_fee: float | None = None,
    sorftime_profit: float | None = None,
    fba_source: str | None = None,
    platform_source: str | None = None,
    landed_cost_source: str | None = None,
    monthly_sales_source: str | None = None,
    price_source: str | None = None,
    ad_rate_source: str | None = None,
    return_rate_source: str | None = None,
    return_processing_fee_source: str | None = None,
    fixed_monthly_source: str | None = None,
    weight_source: str | None = None,
    referral_rate_source: str | None = None,
    sorftime_profit_source: str | None = None,
    source_evidence: dict[str, dict] | None = None,
    as_of: str | None = None,
) -> dict:
    source_evidence = source_evidence or {}
    ad_rate_value = 0.15 if ad_rate is None else ad_rate
    return_rate_value = 0.05 if return_rate is None else return_rate
    return_processing_fee_value = 3.5 if return_processing_fee is None else return_processing_fee
    fixed_monthly_value = 500.0 if fixed_monthly is None else fixed_monthly
    numeric = {
        "price": price, "landed_cost": landed_cost, "weight_kg": weight_kg,
        "referral_rate": referral_rate, "ad_rate": ad_rate_value, "return_rate": return_rate_value,
        "return_processing_fee": return_processing_fee_value, "fixed_monthly": fixed_monthly_value,
    }
    if fba_fee is not None: numeric["fba_fee"] = fba_fee
    if platform_fee is not None: numeric["platform_fee"] = platform_fee
    if monthly_sales is not None: numeric["monthly_sales"] = monthly_sales
    if sorftime_profit is not None: numeric["sorftime_profit"] = sorftime_profit
    bool_inputs = [name for name, value in numeric.items() if isinstance(value, bool)]
    if bool_inputs:
        raise ValueError(f"boolean values are not valid numeric inputs: {bool_inputs}")
    non_numeric = [name for name, value in numeric.items() if not isinstance(value, numbers.Real)]
    if non_numeric:
        raise ValueError(f"non-numeric inputs: {non_numeric}")
    invalid = []
    for name, value in numeric.items():
        try:
            finite = math.isfinite(float(value))
        except (OverflowError, TypeError, ValueError):
            finite = False
        if not finite:
            invalid.append(name)
    if invalid:
        raise ValueError(f"non-finite numeric inputs: {invalid}")
    if price <= 0:
        raise ValueError("price must be > 0")
    if landed_cost < 0:
        raise ValueError("landed_cost must be >= 0")
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    if fba_fee is not None and fba_fee < 0:
        raise ValueError("fba_fee must be >= 0")
    if platform_fee is not None and platform_fee < 0:
        raise ValueError("platform_fee must be >= 0")
    if monthly_sales is not None and monthly_sales <= 0:
        raise ValueError("monthly_sales must be > 0")
    for name, value in {"referral_rate": referral_rate, "ad_rate": ad_rate_value, "return_rate": return_rate_value}.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")
    if return_processing_fee_value < 0 or fixed_monthly_value < 0:
        raise ValueError("fees and fixed_monthly must be >= 0")

    fba_estimated = estimate_fba_fee(weight_kg)
    fba_used = float(fba_fee) if fba_fee is not None else fba_estimated
    fba_source_label = "ESTIMATED_FORMULA" if fba_fee is None else (fba_source or "USER_INPUT_UNVERIFIED")
    platform_fee_used = float(platform_fee) if platform_fee is not None else price * referral_rate
    platform_source_label = "ESTIMATED_RATE" if platform_fee is None else (platform_source or "USER_INPUT_UNVERIFIED")

    amazon_fee_contribution = price - fba_used - platform_fee_used
    product_gross_profit = amazon_fee_contribution - landed_cost
    ad_cost = price * ad_rate_value
    return_allowance = return_rate_value * (landed_cost + fba_used + return_processing_fee_value)
    operating_contribution = product_gross_profit - ad_cost - return_allowance
    operating_margin = operating_contribution / price * 100 if price else 0.0

    sorftime_check = None
    if sorftime_profit is not None:
        delta = amazon_fee_contribution - float(sorftime_profit)
        sorftime_check = {
            "reported": float(sorftime_profit),
            "recomputed": amazon_fee_contribution,
            "delta": delta,
            "matches": abs(delta) <= 0.02,
            "interpretation": "price - FBA - platform fee; before landed cost/ads/returns/fixed costs",
        }

    fba_delta = fba_used - fba_estimated
    monthly_effect = fba_delta * monthly_sales if monthly_sales is not None else None
    net_monthly = operating_contribution * monthly_sales - fixed_monthly_value if monthly_sales is not None else None
    breakeven_units = fixed_monthly_value / operating_contribution if operating_contribution > 0 else None

    quality = {
        "price": _source_status(price_source, price > 0, "price"),
        "fba": _source_status(fba_source_label, True, "fba"),
        "platform_fee": _source_status(platform_source_label, True, "platform_fee"),
        "landed_cost": _source_status(landed_cost_source, True, "landed_cost"),
        "monthly_sales": _source_status(monthly_sales_source, monthly_sales is not None, "monthly_sales"),
        "ad_rate": _source_status("DEFAULT_ASSUMED" if ad_rate is None else (ad_rate_source or "USER_INPUT_UNVERIFIED"), True, "ad_rate"),
        "return_rate": _source_status("DEFAULT_ASSUMED" if return_rate is None else (return_rate_source or "USER_INPUT_UNVERIFIED"), True, "return_rate"),
        "return_processing_fee": _source_status("DEFAULT_ASSUMED" if return_processing_fee is None else (return_processing_fee_source or "USER_INPUT_UNVERIFIED"), True, "return_processing_fee"),
        "fixed_monthly": _source_status("DEFAULT_ASSUMED" if fixed_monthly is None else (fixed_monthly_source or "USER_INPUT_UNVERIFIED"), True, "fixed_monthly"),
        "weight": _source_status(weight_source, fba_fee is None, "weight") if fba_fee is None else "NOT_USED",
        "referral_rate": _source_status(referral_rate_source, platform_fee is None, "referral_rate") if platform_fee is None else "NOT_USED",
    }
    if sorftime_check is not None:
        source_status = _source_status(sorftime_profit_source, True, "sorftime_profit")
        quality["sorftime_profit"] = "MISMATCH" if not sorftime_check["matches"] else source_status
    blocking = [name for name, status in quality.items() if status in {"MISSING", "UNVERIFIED", "MISMATCH"}]
    estimated = [name for name, status in quality.items() if status == "ESTIMATED"]
    if blocking:
        decision_status = "BLOCKED: unverified/missing sources: " + ", ".join(blocking)
    elif estimated:
        decision_status = "PROVISIONAL: estimated sources: " + ", ".join(estimated)
    else:
        required_evidence = [
            "price",
            "fba",
            "platform_fee",
            "landed_cost",
            "monthly_sales",
            "ad_rate",
            "return_rate",
            "return_processing_fee",
            "fixed_monthly",
        ]
        invalid_evidence = []
        for field in required_evidence:
            evidence = source_evidence.get(field)
            if (
                not isinstance(evidence, dict)
                or evidence.get("evidence_type") in {None, "assumption"}
                or not isinstance(evidence.get("normalized_value"), numbers.Real)
                or isinstance(evidence.get("normalized_value"), bool)
                or not math.isfinite(float(evidence["normalized_value"]))
            ):
                invalid_evidence.append(field)
        if invalid_evidence:
            decision_status = "BLOCKED: missing verified source evidence: " + ", ".join(invalid_evidence)
        elif operating_contribution <= 0:
            decision_status = "NO-GO: operating contribution is not positive"
        else:
            decision_status = "READY_FOR_GO_NO_GO_REVIEW"

    return {
        "price": price,
        "landed_cost": landed_cost,
        "weight_kg": weight_kg,
        "fba_fee_used": fba_used,
        "fba_fee_source": fba_source_label,
        "fba_formula_estimate": fba_estimated,
        "fba_delta_vs_formula": fba_delta,
        "fba_monthly_delta_example": monthly_effect,
        "platform_fee_used": platform_fee_used,
        "platform_fee_source": platform_source_label,
        "referral_rate_assumption": referral_rate,
        "amazon_fee_contribution": amazon_fee_contribution,
        "product_gross_profit_after_landed_cost": product_gross_profit,
        "ad_cost_assumption": ad_cost,
        "return_allowance": return_allowance,
        "operating_contribution": operating_contribution,
        "operating_margin_pct": operating_margin,
        "monthly_sales": monthly_sales,
        "net_monthly_profit": net_monthly,
        "breakeven_units_per_month": breakeven_units,
        "decision_status": decision_status,
        "source_dates": {"as_of": as_of} if as_of else {},
        "data_quality": quality,
        "source_evidence": source_evidence or {},
        "sorftime_profit_check": sorftime_check,
        "assumptions": {
            "ad_rate": ad_rate_value,
            "return_rate": return_rate_value,
            "return_processing_fee": return_processing_fee_value,
            "fixed_monthly": fixed_monthly_value,
            "sources": {
                "ad_rate": "DEFAULT_ASSUMED" if ad_rate is None else (ad_rate_source or "USER_INPUT_UNVERIFIED"),
                "return_rate": "DEFAULT_ASSUMED" if return_rate is None else (return_rate_source or "USER_INPUT_UNVERIFIED"),
                "return_processing_fee": "DEFAULT_ASSUMED" if return_processing_fee is None else (return_processing_fee_source or "USER_INPUT_UNVERIFIED"),
                "fixed_monthly": "DEFAULT_ASSUMED" if fixed_monthly is None else (fixed_monthly_source or "USER_INPUT_UNVERIFIED"),
            },
        },
        "semantics": {
            "amazon_fee_contribution": "price - FBA - platform fee; Sorftime profit/gross_profit matches this before other costs",
            "product_gross_profit_after_landed_cost": "Amazon fee contribution - landed cost",
            "operating_contribution": "after ad and return allowance, before fixed monthly costs",
            "net_monthly_profit": "operating contribution * monthly sales - fixed monthly; only meaningful when inputs are verified",
        },
    }


def _fmt(value):
    if value is None:
        return "未提供"
    if isinstance(value, float):
        return f"${value:.2f}"
    return str(value)


def main() -> int:
    p = argparse.ArgumentParser(description="Amazon P&L with explicit data-quality gates")
    p.add_argument("--price", type=float)
    p.add_argument("--landed-cost", "--cost", dest="landed_cost", type=float)
    p.add_argument("--weight", type=float, default=0.5, help="kg")
    p.add_argument("--fba-fee", type=float, help="ProductRequest.FbaFee; preferred over formula")
    p.add_argument("--platform-fee", type=float, help="ProductRequest.PlatformFee")
    p.add_argument("--referral-rate", type=float, default=0.15)
    p.add_argument("--ad-rate", type=float, help="ad cost / price; defaults to 0.15 as DEFAULT_ASSUMED")
    p.add_argument("--return-rate", type=float, help="return rate; defaults to 0.05 as DEFAULT_ASSUMED")
    p.add_argument("--return-processing-fee", type=float)
    p.add_argument("--fixed-monthly", type=float)
    p.add_argument("--monthly-sales", type=float)
    p.add_argument("--fba-source", help="verified / product_detail / user_verified / estimated / user_estimate / unknown")
    p.add_argument("--platform-source", help="verified / product_detail / estimated / unknown")
    p.add_argument("--landed-cost-source", help="verified / supplier_confirmed / user_verified / estimated / unknown")
    p.add_argument("--monthly-sales-source", help="verified / product_detail / estimated / unknown")
    p.add_argument("--price-source", help="verified / product_detail / user_verified / estimated / unknown")
    p.add_argument("--ad-rate-source")
    p.add_argument("--return-rate-source")
    p.add_argument("--return-processing-fee-source")
    p.add_argument("--fixed-monthly-source")
    p.add_argument("--weight-source")
    p.add_argument("--referral-rate-source")
    p.add_argument("--sorftime-profit-source")
    p.add_argument("--as-of", help="source timestamp, ISO-8601")
    p.add_argument("--sorftime-profit", "--sorftime-gross-profit", dest="sorftime_profit", type=float, help="Check Sorftime product_detail.profit (legacy gross_profit) semantics")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.price is None or args.landed_cost is None:
        demo = compute(
            price=24.99,
            landed_cost=6.5,
            weight_kg=2.009,
            fba_fee=8.90,
            platform_fee=3.06,
            monthly_sales=8237,
            sorftime_profit=13.03,
            price_source="verified",
            fba_source="verified",
            platform_source="verified",
            landed_cost_source="estimated",
            monthly_sales_source="verified",
            ad_rate_source="verified",
            return_rate_source="verified",
            return_processing_fee_source="verified",
            fixed_monthly_source="verified",
            weight_source="verified",
            referral_rate_source="verified",
            sorftime_profit_source="verified",
            as_of="2026-10-27",
        )
        print(json.dumps({"demo": demo}, ensure_ascii=False, indent=2))
        return 0

    try:
        result = compute(
            price=args.price,
            landed_cost=args.landed_cost,
            weight_kg=args.weight,
            referral_rate=args.referral_rate,
            platform_fee=args.platform_fee,
            ad_rate=args.ad_rate,
            return_rate=args.return_rate,
            return_processing_fee=args.return_processing_fee,
            fixed_monthly=args.fixed_monthly,
            monthly_sales=args.monthly_sales,
            fba_fee=args.fba_fee,
            sorftime_profit=args.sorftime_profit,
            fba_source=args.fba_source,
            platform_source=args.platform_source,
            landed_cost_source=args.landed_cost_source,
            monthly_sales_source=args.monthly_sales_source,
            price_source=args.price_source,
            ad_rate_source=args.ad_rate_source,
            return_rate_source=args.return_rate_source,
            return_processing_fee_source=args.return_processing_fee_source,
            fixed_monthly_source=args.fixed_monthly_source,
            weight_source=args.weight_source,
            referral_rate_source=args.referral_rate_source,
            sorftime_profit_source=args.sorftime_profit_source,
            as_of=args.as_of,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("# Amazon P&L")
        print(f"- 售价: {_fmt(result['price'])}")
        print(f"- 到岸成本: {_fmt(result['landed_cost'])}")
        print(f"- FBA: {_fmt(result['fba_fee_used'])} ({result['fba_fee_source']})")
        print(f"- Amazon 费用后贡献: {_fmt(result['amazon_fee_contribution'])}")
        print(f"- 采购后毛利: {_fmt(result['product_gross_profit_after_landed_cost'])}")
        print(f"- 广告: {_fmt(result['ad_cost_assumption'])}")
        print(f"- 退货计提: {_fmt(result['return_allowance'])}")
        print(f"- 经营贡献: {_fmt(result['operating_contribution'])} ({result['operating_margin_pct']:.1f}%)")
        print(f"- 月净利: {_fmt(result['net_monthly_profit'])}")
        print(f"- 决策状态: {result['decision_status']}")
        if result["sorftime_profit_check"]:
            c = result["sorftime_profit_check"]
            print(f"- Sorftime profit校验: {'PASS' if c['matches'] else 'FAIL'} (delta ${c['delta']:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
