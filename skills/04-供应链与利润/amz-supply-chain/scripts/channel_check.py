#!/usr/bin/env python3
"""
Sorftime 双通道检测脚本（MCP + CLI）
所有 amz-* Skill 共用。检测当前环境是否配置了 Sorftime 访问凭证，
并给出通道选择建议或注册引导。

退出码：
  0 = 至少有一个可用通道
  1 = 无任何凭证
"""
import os
import sys
import subprocess
import json

REGISTRATION_URL = "https://open.sorftime.com/home?tag=NTIw"
GUIDE_TEXT = (
    "未检测到 Sorftime 访问凭证。\n"
    f"请通过 {REGISTRATION_URL} 注册并领用 7 天试用，"
    "获取 Account-SK 后告诉我，我帮你一键配置。\n"
    "MCP 适合 AI Agent 直接调用，CLI 适合脚本化批量拉取。"
)


def check_mcp() -> bool:
    """检测 MCP 通道：环境变量 SORFTIME_MCP_KEY 是否存在且非空"""
    key = os.environ.get("SORFTIME_MCP_KEY", "").strip()
    return bool(key)


def check_cli() -> bool:
    """检测 CLI 通道：sorftime 命令可用且已配置 profile"""
    # 1. 命令是否存在
    try:
        result = subprocess.run(
            ["which", "sorftime"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False
    except Exception:
        return False

    # 2. 尝试 whoami（已登录则返回 0）
    try:
        result = subprocess.run(
            ["sorftime", "whoami"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass

    # 3. 检查配置目录是否存在（~/.sorftime/）
    config_dir = os.path.expanduser("~/.sorftime")
    if os.path.isdir(config_dir):
        # 检查是否有配置文件
        for fname in os.listdir(config_dir):
            if fname.endswith((".json", ".yaml", ".yml", ".toml", ".conf", ".ini")):
                return True

    return False


def main():
    mcp_ok = check_mcp()
    cli_ok = check_cli()

    result = {
        "mcp_available": mcp_ok,
        "cli_available": cli_ok,
        "recommended_channel": None,
        "message": "",
    }

    if mcp_ok and cli_ok:
        result["recommended_channel"] = "mcp"
        result["message"] = "MCP+CLI 均可用，默认使用 MCP"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    elif mcp_ok:
        result["recommended_channel"] = "mcp"
        result["message"] = "仅 MCP 通道可用"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    elif cli_ok:
        result["recommended_channel"] = "cli"
        result["message"] = "仅 CLI 通道可用"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    else:
        result["message"] = GUIDE_TEXT
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        print(GUIDE_TEXT, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
