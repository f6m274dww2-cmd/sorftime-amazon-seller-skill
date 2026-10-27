#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazon data evidence ledger.

Purpose:
- record MCP/CLI/public responses with exact tool, params, channel and time;
- compute a SHA-256 digest over canonical JSON to detect later tampering;
- verify a decision-grade evidence set before a Go/No-Go or purchase action;
- capture Sorftime CLI responses directly so sellers do not hand-copy numbers.

This proves capture integrity, not upstream truth by itself. Upstream truth still
depends on the Sorftime credential, service response and reproducible parameters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA_VERSION = "amz-evidence-v1"
EVIDENCE_TYPES = {"observed", "derived", "estimate", "inference", "missing"}
CHANNELS = {"mcp", "cli", "public", "manual", "derived"}
SENSITIVE_KEYS = {
    "api_key", "apikey", "token", "access_token", "secret", "client_secret",
    "password", "authorization", "cookie", "account_sk", "account-s-k",
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: Optional[datetime] = None) -> str:
    return (value or now_utc()).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError("时间必须带时区，例如 2026-10-27T15:00:00+08:00 或 ...Z")
    return dt.astimezone(timezone.utc)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


EMPTY_MARKERS = (
    "no data available", "no relevant data", "no product found",
    "please specify", "please enter", "not found", "无数据", "未找到",
)


def is_empty_payload(value: Any) -> bool:
    """Treat tool empty sentinels as missing evidence, not observed facts."""
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip().lower().rstrip(".!。")
        return not text or text in EMPTY_MARKERS
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return True
    if isinstance(value, dict):
        for key in ("data", "Data", "message", "Message", "msg"):
            child = value.get(key)
            if isinstance(child, str):
                child_text = child.strip().lower().rstrip(".!。")
                if not child_text or child_text in EMPTY_MARKERS:
                    return True
    return False


def _sensitive_paths(value: Any, prefix: str = "") -> List[str]:
    found: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.lower().replace(" ", "_") in SENSITIVE_KEYS and child not in (None, "", [], {}):
                found.append(path)
            found.extend(_sensitive_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_sensitive_paths(child, f"{prefix}[{index}]"))
    return found


def _load_json_arg(text: str, label: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} 不是合法 JSON: {exc}") from exc


def _read_payload(path: str) -> Any:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).expanduser().read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"响应文件不是合法 JSON: {exc}") from exc


def _extract_json(text: str) -> Any:
    cleaned = re.sub(r"\x1b\[[0-9;]*[mK]", "", text).replace("\r", "")
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", cleaned):
        candidate = cleaned[match.start():]
        try:
            value, _ = decoder.raw_decode(candidate)
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("CLI 输出中找不到合法 JSON")


def _api_code(payload: Any) -> Optional[Any]:
    if isinstance(payload, dict):
        return payload.get("Code", payload.get("code"))
    return None


def _append_record(ledger: Path, record: Dict[str, Any]) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def make_record(
    *,
    tool: str,
    params: Dict[str, Any],
    stage: str,
    channel: str,
    payload: Any,
    evidence_type: str,
    observed_at: str,
    source_label: str,
    derived_from: Optional[List[str]] = None,
    formula: Optional[str] = None,
    notes: Optional[str] = None,
    transport: Optional[Dict[str, Any]] = None,
    allow_sensitive: bool = False,
) -> Dict[str, Any]:
    if evidence_type not in EVIDENCE_TYPES:
        raise ValueError(f"evidence_type 必须是 {sorted(EVIDENCE_TYPES)}")
    if channel not in CHANNELS:
        raise ValueError(f"channel 必须是 {sorted(CHANNELS)}")
    if not re.fullmatch(r"G[0-9]+", stage):
        raise ValueError("stage 必须形如 G0、G1、...、G9")
    sensitive = _sensitive_paths(payload) + _sensitive_paths(params) + _sensitive_paths(transport or {})
    if sensitive and not allow_sensitive:
        raise ValueError(
            "检测到疑似密钥字段，拒绝写入证据台账: " + ", ".join(sensitive[:8]) +
            "。请先脱敏；确需保留请显式加 --allow-sensitive。"
        )
    if evidence_type == "observed" and is_empty_payload(payload):
        evidence_type = "missing"
        notes = ((notes + "；") if notes else "") + "工具返回空数据/空结果，自动标记为 missing，不进入 decision-grade。"
    observed = parse_time(observed_at)
    recorded = now_utc()
    digest = sha256_bytes(canonical_bytes(payload))
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"ev-{recorded.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}",
        "evidence_type": evidence_type,
        "tool": tool,
        "channel": channel,
        "stage": stage,
        "params": params,
        "observed_at": iso_utc(observed),
        "recorded_at": iso_utc(recorded),
        "source_label": source_label,
        "payload_sha256": digest,
        "payload": payload,
        "derived_from": derived_from or [],
        "formula": formula,
        "notes": notes or "",
        "transport": transport or {},
    }


def record_command(args: argparse.Namespace) -> int:
    payload = _read_payload(args.input)
    params = _load_json_arg(args.params, "--params")
    if not isinstance(params, dict):
        raise ValueError("--params 必须是 JSON 对象")
    record = make_record(
        tool=args.tool,
        params=params,
        stage=args.stage,
        channel=args.channel,
        payload=payload,
        evidence_type=args.evidence_type,
        observed_at=args.observed_at or iso_utc(),
        source_label=args.source_label or args.tool,
        derived_from=args.derived_from,
        formula=args.formula,
        notes=args.notes,
        allow_sensitive=args.allow_sensitive,
    )
    _append_record(Path(args.ledger).expanduser(), record)
    if args.json:
        print(json.dumps({"ok": True, "record": record}, ensure_ascii=False, indent=2))
    else:
        print(f"已写入证据: {record['record_id']}")
        print(f"tool={record['tool']} stage={record['stage']} channel={record['channel']}")
        print(f"payload_sha256={record['payload_sha256']}")
        print(f"ledger={Path(args.ledger).expanduser()}")
    return 0


def capture_cli_command(args: argparse.Namespace) -> int:
    params = _load_json_arg(args.params, "--params")
    if not isinstance(params, dict):
        raise ValueError("--params 必须是 JSON 对象")
    import shutil
    if not shutil.which("sorftime"):
        print("ERROR: 找不到 sorftime CLI。请先安装并配置 sorftime-cli。", file=sys.stderr)
        return 2
    cmd = ["sorftime", "api", args.endpoint, json.dumps(params, ensure_ascii=False, separators=(",", ":")), "--domain", str(args.domain)]
    if args.profile:
        cmd.extend(["--profile", args.profile])
    started = iso_utc()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"ERROR: Sorftime CLI 超时 ({args.timeout}s)", file=sys.stderr)
        return 2
    try:
        payload = _extract_json(proc.stdout)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr[-1000:], file=sys.stderr)
        return 2
    code = _api_code(payload)
    business_ok = code in (None, 0, "0")
    if proc.returncode != 0 or not business_ok:
        if not args.record_errors:
            print(f"ERROR: CLI 失败 exit={proc.returncode} api_code={code}", file=sys.stderr)
            return 2
    transport = {
        "command": cmd,
        "profile": args.profile or "",
        "domain": args.domain,
        "started_at": started,
        "exit_code": proc.returncode,
        "api_code": code,
        "stdout_sha256": sha256_bytes(proc.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(proc.stderr.encode("utf-8")),
    }
    record = make_record(
        tool=args.endpoint,
        params=params,
        stage=args.stage,
        channel="cli",
        payload=payload,
        evidence_type="observed",
        observed_at=iso_utc(),
        source_label=args.source_label or "Sorftime CLI",
        notes=args.notes,
        transport=transport,
        allow_sensitive=args.allow_sensitive,
    )
    _append_record(Path(args.ledger).expanduser(), record)
    if args.raw_dir:
        raw_dir = Path(args.raw_dir).expanduser()
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{record['record_id']}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (raw_dir / f"{record['record_id']}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    print(f"已采集并写入证据: {record['record_id']}")
    print(f"evidence_type={record['evidence_type']}")
    print(f"payload_sha256={record['payload_sha256']}")
    print(f"ledger={Path(args.ledger).expanduser()}")
    if record["evidence_type"] == "missing":
        print("WARN: 工具返回空数据，已记为 missing；该记录不能支撑 decision-grade。", file=sys.stderr)
    if proc.returncode != 0 or not business_ok:
        print(f"WARN: 已记录失败响应 exit={proc.returncode} api_code={code}", file=sys.stderr)
        return 2
    return 0


def _read_ledger(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    records: List[Dict[str, Any]] = []
    errors: List[str] = []
    if not path.exists():
        return records, [f"台账不存在: {path}"]
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"第 {line_no} 行不是 JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"第 {line_no} 行不是 JSON 对象")
            continue
        records.append(value)
    return records, errors


def _validate_record(record: Dict[str, Any], *, max_future_minutes: int, fresh_hours: Optional[float]) -> List[str]:
    errors: List[str] = []
    required = [
        "schema_version", "record_id", "evidence_type", "tool", "channel", "stage",
        "params", "observed_at", "recorded_at", "source_label", "payload_sha256", "payload",
    ]
    for key in required:
        if key not in record:
            errors.append(f"缺少字段 {key}")
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 不是 {SCHEMA_VERSION}")
    if record.get("evidence_type") not in EVIDENCE_TYPES:
        errors.append("evidence_type 非法")
    if record.get("channel") not in CHANNELS:
        errors.append("channel 非法")
    if not isinstance(record.get("params"), dict):
        errors.append("params 不是对象")
    stage = record.get("stage")
    if not isinstance(stage, str) or not re.fullmatch(r"G[0-9]+", stage):
        errors.append("stage 非法")
    try:
        observed = parse_time(str(record.get("observed_at", "")))
        recorded = parse_time(str(record.get("recorded_at", "")))
        now = now_utc()
        if observed > now + timedelta(minutes=max_future_minutes):
            errors.append("observed_at 在未来")
        if recorded > now + timedelta(minutes=max_future_minutes):
            errors.append("recorded_at 在未来")
        if fresh_hours is not None and now - observed > timedelta(hours=fresh_hours):
            errors.append(f"证据已超过 {fresh_hours:g} 小时新鲜度")
    except Exception as exc:
        errors.append(f"时间格式非法: {exc}")
    if "payload" in record:
        try:
            actual = sha256_bytes(canonical_bytes(record["payload"]))
        except Exception as exc:
            errors.append(f"payload 无法规范化: {exc}")
        else:
            if actual != record.get("payload_sha256"):
                errors.append("payload_sha256 不匹配，内容可能被篡改")
    if record.get("evidence_type") == "derived":
        if not record.get("derived_from"):
            errors.append("derived 记录缺少 derived_from")
        if not record.get("formula"):
            errors.append("derived 记录缺少 formula")
    if record.get("evidence_type") == "observed" and is_empty_payload(record.get("payload")):
        errors.append("observed 记录包含空数据，应标记为 missing")
    return errors


def verify_command(args: argparse.Namespace) -> int:
    path = Path(args.ledger).expanduser()
    records, errors = _read_ledger(path)
    seen: Dict[str, int] = {}
    valid_records: List[Dict[str, Any]] = []
    for index, record in enumerate(records, 1):
        record_errors = _validate_record(
            record,
            max_future_minutes=args.max_future_minutes,
            fresh_hours=args.fresh_hours,
        )
        rid = str(record.get("record_id", ""))
        if rid:
            seen[rid] = seen.get(rid, 0) + 1
        if record_errors:
            errors.extend(f"记录 {rid or index}: {e}" for e in record_errors)
        else:
            valid_records.append(record)
    for rid, count in seen.items():
        if count > 1:
            errors.append(f"record_id 重复: {rid} x{count}")
    observed_records = [r for r in valid_records if r.get("evidence_type") == "observed"]
    if args.decision_grade:
        pool = observed_records
        if len(pool) < args.min_observed:
            errors.append(f"decision-grade 至少需要 {args.min_observed} 条 observed 记录，当前 {len(pool)}")
    else:
        pool = valid_records
    for stage in args.require_stage:
        if not any(r.get("stage") == stage for r in pool):
            errors.append(f"缺少 {stage} 的{'observed ' if args.decision_grade else ''}证据")
    for tool in args.require_tool:
        if not any(r.get("tool") == tool for r in pool):
            errors.append(f"缺少工具 {tool} 的{'observed ' if args.decision_grade else ''}证据")
    summary = {
        "ok": not errors,
        "ledger": str(path),
        "records": len(records),
        "valid_records": len(valid_records),
        "observed_records": len(observed_records),
        "by_stage": _count_by(valid_records, "stage"),
        "by_channel": _count_by(valid_records, "channel"),
        "by_type": _count_by(valid_records, "evidence_type"),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"台账校验: {'PASS' if summary['ok'] else 'FAIL'}")
        print(f"记录={summary['records']} 有效={summary['valid_records']} observed={summary['observed_records']}")
        if summary["errors"]:
            for error in summary["errors"]:
                print(f"- {error}")
    return 0 if summary["ok"] else 1


def _count_by(records: Sequence[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for record in records:
        value = str(record.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def summary_command(args: argparse.Namespace) -> int:
    records, errors = _read_ledger(Path(args.ledger).expanduser())
    print(json.dumps({
        "ledger": str(Path(args.ledger).expanduser()),
        "records": len(records),
        "by_stage": _count_by(records, "stage"),
        "by_channel": _count_by(records, "channel"),
        "by_type": _count_by(records, "evidence_type"),
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def reproduce_command(args: argparse.Namespace) -> int:
    records, _ = _read_ledger(Path(args.ledger).expanduser())
    match = next((r for r in records if r.get("record_id") == args.record_id), None)
    if match is None:
        print(f"ERROR: 找不到 record_id={args.record_id}", file=sys.stderr)
        return 1
    transport = match.get("transport") or {}
    output = {
        "record_id": match.get("record_id"),
        "tool": match.get("tool"),
        "params": match.get("params"),
        "stage": match.get("stage"),
        "channel": match.get("channel"),
        "observed_at": match.get("observed_at"),
        "payload_sha256": match.get("payload_sha256"),
        "command": transport.get("command"),
        "note": "重放会产生新的 observed_at，因此 payload 变化不一定代表原记录有误；应比较关键业务字段。",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Amazon data evidence ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="记录一份已有 MCP/公开源响应")
    rec.add_argument("--ledger", required=True)
    rec.add_argument("--tool", required=True)
    rec.add_argument("--stage", required=True)
    rec.add_argument("--channel", choices=sorted(CHANNELS), default="mcp")
    rec.add_argument("--params", default="{}")
    rec.add_argument("--input", default="-", help="JSON 响应文件；- 表示 stdin")
    rec.add_argument("--evidence-type", choices=sorted(EVIDENCE_TYPES), default="observed")
    rec.add_argument("--observed-at")
    rec.add_argument("--source-label")
    rec.add_argument("--notes")
    rec.add_argument("--derived-from", action="append", default=[])
    rec.add_argument("--formula")
    rec.add_argument("--allow-sensitive", action="store_true")
    rec.add_argument("--json", action="store_true")
    rec.set_defaults(func=record_command)

    cap = sub.add_parser("capture-cli", help="直接调用 Sorftime CLI 并落账")
    cap.add_argument("--ledger", required=True)
    cap.add_argument("--endpoint", required=True)
    cap.add_argument("--stage", required=True)
    cap.add_argument("--params", default="{}")
    cap.add_argument("--domain", type=int, default=1)
    cap.add_argument("--profile")
    cap.add_argument("--timeout", type=int, default=120)
    cap.add_argument("--source-label")
    cap.add_argument("--notes")
    cap.add_argument("--raw-dir")
    cap.add_argument("--record-errors", action="store_true")
    cap.add_argument("--allow-sensitive", action="store_true")
    cap.set_defaults(func=capture_cli_command)

    ver = sub.add_parser("verify", help="校验哈希、时间、工具、参数与阶段完整性")
    ver.add_argument("--ledger", required=True)
    ver.add_argument("--decision-grade", action="store_true")
    ver.add_argument("--require-stage", action="append", default=[])
    ver.add_argument("--require-tool", action="append", default=[])
    ver.add_argument("--min-observed", type=int, default=1)
    ver.add_argument("--fresh-hours", type=float)
    ver.add_argument("--max-future-minutes", type=int, default=5)
    ver.add_argument("--json", action="store_true")
    ver.set_defaults(func=verify_command)

    summ = sub.add_parser("summary", help="查看台账统计")
    summ.add_argument("--ledger", required=True)
    summ.set_defaults(func=summary_command)

    rep = sub.add_parser("reproduce", help="输出可复核命令与参数")
    rep.add_argument("--ledger", required=True)
    rep.add_argument("--record-id", required=True)
    rep.set_defaults(func=reproduce_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
