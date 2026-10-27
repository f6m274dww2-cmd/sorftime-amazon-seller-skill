#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified Sorftime patent caller: MCP / HTTP API / CLI.

MCP uses snake_case tool names and lowercase params.
HTTP API and sorftime-cli use PascalCase endpoints and PascalCase params.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

TOOL_ENDPOINT = {
    "patent_search_from_keyword": "PatentSearchFromKeyword",
    "patent_search_from_image": "PatentSearchFromImage",
    "patent_request": "PatentRequest",
}
PARAM_MAP = {
    "keyword": "Keyword",
    "image": "Image",
    "query_mode": "QueryMode",
    "country": "Country",
    "legal_status": "LegalStatus",
    "patent_type": "PatentType",
    "product_keyword": "ProductKeyword",
    "applicant": "Applicant",
    "publication_no": "PublicationNo",
    "application_no": "ApplicationNo",
    "class_type": "ClassType",
    "class_no": "ClassNo",
    "loc_class_no": "LocClassNo",
    "page_index": "PageIndex",
}


def to_pascal_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {PARAM_MAP.get(key, key[:1].upper() + key[1:] if key else key): value for key, value in params.items()}


def extract_json(text: str) -> Any:
    clean = re.sub(r"\x1b\[[0-9;]*[mK]", "", text).replace("\r", "")
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", clean):
        try:
            value, _ = decoder.raw_decode(clean[match.start():])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("响应中没有合法 JSON")


def seller_agent_scripts() -> Path:
    script = Path(__file__).resolve()
    # Source layout has a category directory; installed layout is flattened.
    for parent in script.parents:
        for candidate in (
            parent / "sorftime-seller-agent" / "scripts",
            parent / "00-Sorftime数据层" / "sorftime-seller-agent" / "scripts",
        ):
            if (candidate / "utils" / "mcp_client.py").exists():
                return candidate
    raise RuntimeError("MCP 通道不可用：未找到 sorftime-seller-agent/scripts/utils/mcp_client.py")


def call_mcp(tool: str, params: Dict[str, Any]) -> Any:
    scripts = seller_agent_scripts()
    if not (scripts / "utils" / "mcp_client.py").exists():
        raise RuntimeError(f"MCP 通道不可用：未找到 {scripts / 'utils' / 'mcp_client.py'}")
    sys.path.insert(0, str(scripts))
    from utils.mcp_client import call_tool_json
    return call_tool_json("sorftime_raw_call", {"tool_name": tool, "arguments": params})


def call_cli(tool: str, params: Dict[str, Any], domain: int, timeout: int) -> Any:
    endpoint = TOOL_ENDPOINT[tool]
    cmd = [
        "sorftime", "api", endpoint,
        json.dumps(to_pascal_params(params), ensure_ascii=False, separators=(",", ":")),
        "--domain", str(domain),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[-1600:])
    return extract_json(proc.stdout)


def _account_sk() -> str:
    env_key = os.getenv("SORFTIME_ACCOUNT_SK", "").strip()
    if env_key:
        return env_key
    config = Path.home() / ".sorftime" / "config.json"
    data = json.loads(config.read_text(encoding="utf-8"))
    current = data.get("currentProfile")
    profiles = {item.get("name"): item for item in data.get("profiles", [])}
    profile = profiles.get(current) or (data.get("profiles") or [None])[0]
    if not profile or not profile.get("accountSK"):
        raise RuntimeError("未找到 Sorftime Account-SK，请先运行 sorftime add/use")
    return str(profile["accountSK"])


def call_api(tool: str, params: Dict[str, Any], domain: int, timeout: int) -> Any:
    endpoint = TOOL_ENDPOINT[tool]
    url = f"https://cli.sorftime.com/api/{endpoint}?domain={domain}"
    body = json.dumps(to_pascal_params(params), ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"BasicAuth {_account_sk()}",
            "Browser": "Cli",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def auto_channel() -> str:
    try:
        scripts = seller_agent_scripts()
    except RuntimeError:
        scripts = None
    if scripts and (Path.home() / ".sorftime" / "env").exists():
        return "mcp"
    if (Path.home() / ".sorftime" / "config.json").exists():
        return "api"
    return "cli"


def main() -> int:
    p = argparse.ArgumentParser(description="Sorftime patent unified caller")
    p.add_argument("--channel", choices=["auto", "mcp", "api", "cli"], default="auto")
    p.add_argument("--tool", required=True, choices=sorted(TOOL_ENDPOINT))
    p.add_argument("--params", default="{}", help="snake_case JSON object")
    p.add_argument("--domain", type=int, default=1)
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    params = json.loads(args.params)
    if not isinstance(params, dict):
        raise ValueError("--params 必须是 JSON 对象")
    channel = auto_channel() if args.channel == "auto" else args.channel
    if channel == "mcp":
        result = call_mcp(args.tool, params)
    elif channel == "api":
        result = call_api(args.tool, params, args.domain, args.timeout)
    else:
        result = call_cli(args.tool, params, args.domain, args.timeout)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"saved={args.output.resolve()} channel={channel} tool={args.tool}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
