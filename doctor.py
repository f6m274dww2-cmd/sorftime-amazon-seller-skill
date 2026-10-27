#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-install readiness check for the Amazon seller skill package."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

EXPECTED_SKILLS = {
    "sorftime-seller-agent", "sorftime-data-cli",
    "amz-fullchain-jtbd", "amz-selection", "amz-market-analysis",
    "amz-supply-chain", "amz-profit-calc", "amz-cpc-keywords",
    "amz-listing-creator", "amz-image-creator", "amz-ad-planning",
    "amz-voc-analysis", "amz-competitor-monitor", "sorftime-patent-risk",
    "ecommerce-visual-copywriting", "product-shots-main-image",
    "product-shots-detail-page", "product-shots-image-gen",
}
IMAGE_KEY_ENVS = (
    "OMNIMAAS_API_KEY",
    "PRODUCT_SHOTS_IMAGEN_API_KEY",
    "PRODUCT_SHOTS_IMAGEGEN_API_KEY",
    "RENDER_API_KEY",
    "CANVASFLOW_IMAGEN_API_KEY",
    "CANVASFLOW_IMAGEGEN_API_KEY",
)
IMAGE_KEY_FILES = (
    "~/.product_shots_imagegen_api_key",
    "~/.product_shots_render_api_key",
    "~/.canvasflow_imagegen_api_key",
)


def add(checks: List[Dict[str, Any]], level: str, name: str, ok: bool, detail: str) -> None:
    checks.append({"level": level, "name": name, "ok": ok, "detail": detail})


def run_text(cmd: List[str], timeout: int = 12) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (proc.stdout + "\n" + proc.stderr).strip()
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def check_skills(dest: Path, checks: List[Dict[str, Any]]) -> None:
    missing = sorted(name for name in EXPECTED_SKILLS if not (dest / name / "SKILL.md").exists())
    add(checks, "CORE", "18 个 Skill", not missing, "全部存在" if not missing else "缺失: " + ", ".join(missing))
    shared = {
        "amz-workflow-map.md": dest / "amz-workflow-map.md",
        "evidence_ledger.py": dest / "evidence_ledger.py",
        "doctor.py": dest / "doctor.py",
        "Amazon全链路-卖家版/开始使用.html": dest / "Amazon全链路-卖家版" / "开始使用.html",
    }
    missing_shared = [name for name, path in shared.items() if not path.exists()]
    add(checks, "CORE", "共享文件", not missing_shared, "全部存在" if not missing_shared else "缺失: " + ", ".join(missing_shared))


def check_python(checks: List[Dict[str, Any]]) -> None:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py312 = shutil.which("python3.12")
    ok = sys.version_info >= (3, 10) or bool(py312)
    detail = f"当前 {version}"
    if py312:
        detail += f"；已发现 python3.12: {py312}"
    else:
        detail += "；未发现 python3.12，可用 uv/uvx 安装或运行 3.12"
    add(checks, "RECOMMENDED", "Python 3.10+", ok, detail)
    add(checks, "RECOMMENDED", "Python 3.12", bool(py312), py312 or "未发现 python3.12；sorftime-seller-agent 建议使用 3.12")


def check_data_channel(dest: Path, checks: List[Dict[str, Any]]) -> None:
    channel_scripts = [
        dest / "amz-selection" / "scripts" / "channel_check.py",
        dest / "amz-voc-analysis" / "scripts" / "channel_check.py",
    ]
    result: Dict[str, Any] = {}
    detail = ""
    for script in channel_scripts:
        if not script.exists():
            continue
        output = run_text([sys.executable, str(script)], timeout=30)
        try:
            result = json.loads(output)
            detail = output
            break
        except Exception:
            detail = output[-1000:]
    mcp = bool(result.get("mcp_available"))
    cli = bool(result.get("cli_available"))
    add(checks, "CORE", "Sorftime 数据通道", mcp or cli, detail or "通道检测脚本未找到")
    add(checks, "READY", "MCP", mcp, "可用" if mcp else "未检测到 MCP")
    add(checks, "READY", "Sorftime CLI", cli, "可用" if cli else "未检测到 CLI")


def check_cli_bins(checks: List[Dict[str, Any]]) -> None:
    for name in ("node", "npm", "sorftime", "jq"):
        path = shutil.which(name)
        add(checks, "RECOMMENDED", name, bool(path), path or "未安装；CLI 数据通道可能不可用")


def check_image(dest: Path, checks: List[Dict[str, Any]]) -> None:
    local_gen = Path.home() / ".codex" / "scripts" / "gen-image.sh"
    local_ok = local_gen.exists() and os.access(local_gen, os.X_OK)
    add(checks, "READY", "本机生图通道", local_ok, str(local_gen) + ("（可用，优先使用）" if local_ok else "（未找到或不可执行）"))
    renderer = dest / "product-shots-image-gen" / "scripts" / "generate.py"
    if not renderer.exists():
        add(checks, "OPTIONAL" if local_ok else "CORE", "包内生图渲染器", False, "未找到 product-shots-image-gen/scripts/generate.py")
        return
    output = run_text([sys.executable, str(renderer), "--help"], timeout=20)
    ok = "usage:" in output.lower()
    add(checks, "OPTIONAL" if local_ok else "READY", "包内生图依赖", ok, "generate.py 可启动" if ok else output[-1000:])
    key_found = any(os.environ.get(name) for name in IMAGE_KEY_ENVS)
    key_found = key_found or any(Path(path).expanduser().exists() for path in IMAGE_KEY_FILES)
    add(checks, "OPTIONAL", "包内 Provider Key", key_found, "已配置" if key_found else "未配置；有本机通道时仍可出图，否则只做策略/Prompt")
    image_ready = local_ok or (ok and key_found)
    add(checks, "READY", "生图可用路径", image_ready, "本机 gen-image.sh" if local_ok else ("包内 product-shots-image-gen" if ok and key_found else "未就绪"))
    setup = dest / "product-shots-image-gen" / "scripts" / "setup.sh"
    add(checks, "OPTIONAL", "生图依赖安装脚本", setup.exists(), str(setup) if setup.exists() else "未找到 setup.sh")


def overall(checks: List[Dict[str, Any]]) -> str:
    if any(c["level"] == "CORE" and not c["ok"] for c in checks):
        return "BLOCKED"
    if any(not c["ok"] for c in checks if c["level"] in {"READY", "RECOMMENDED", "CORE"}):
        return "PARTIAL"
    return "READY"


def main() -> int:
    parser = argparse.ArgumentParser(description="Amazon seller skill environment doctor")
    parser.add_argument("--dest", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    dest = args.dest.expanduser().resolve()
    checks: List[Dict[str, Any]] = []
    check_skills(dest, checks)
    check_python(checks)
    check_data_channel(dest, checks)
    check_cli_bins(checks)
    check_image(dest, checks)
    state = overall(checks)
    payload = {"destination": str(dest), "overall": state, "checks": checks}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"环境状态: {state}")
        print(f"安装目录: {dest}")
        for check in checks:
            mark = "OK" if check["ok"] else ("FAIL" if check["level"] == "CORE" else "WARN")
            print(f"[{mark}] {check['name']}: {check['detail']}")
        if state == "BLOCKED":
            print("结论: 核心能力未就绪。先修复 FAIL 项，再运行全链路。")
        elif state == "PARTIAL":
            print("结论: 核心数据链路可用；生图或 Python 3.12 等增强项尚未完全就绪。")
        else:
            print("结论: 核心与增强能力均已就绪。")
        print("")
        print("联系方式：Jennifer 17316743165（微信同号）")
        print("Sorftime 数据入口：https://open.sorftime.com/home?tag=NTIw")
        print(f"企业微信二维码：{dest / 'Amazon全链路-卖家版' / 'docs' / 'sorftime-jennifer-wecom-qr.png'}")
    if args.strict and state != "READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
