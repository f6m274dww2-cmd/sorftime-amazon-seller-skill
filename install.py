#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install Amazon full-chain skills plus self-contained seller documentation."""
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = ROOT / "skills"
from verify_package import verify_package
from verify_installed import verify_installed

SHARED_FILES = [
    "amz-workflow-map.md",
    "SOURCE-NOTICE.md",
    "evidence_ledger.py",
    "doctor.py",
    "requirements-image.txt",
    "THIRD-PARTY-NOTICES.md",
    "RELEASE-NOTES.md",
]
SHARE_FILES = [
    "开始使用.html",
    "亚马逊卖家全链路工作流地图.html",
    "亚马逊卖家全链路工作流地图.png",
    "Amazon全链路作战地图-R4.5.pdf",
    "SOURCE-NOTICE.md",
    "Sorftime-CHANNEL.md",
    "verify_installed.py",
    "manifest.json",
    "doctor.py",
    "evidence_ledger.py",
    "requirements-image.txt",
    "THIRD-PARTY-NOTICES.md",
    "RELEASE-NOTES.md",
]


def ignore_skill_artifacts(directory, names):
    ignored = set()
    for name in names:
        path = Path(directory) / name
        if name in {"__pycache__", ".DS_Store", ".pytest_cache", ".venv", ".git"} or path.suffix == ".pyc":
            ignored.add(name)
        elif ".bak" in name or " 2" in name:
            ignored.add(name)
    return ignored


def discover_skills() -> list[Path]:
    return sorted({p.parent for p in SKILLS_ROOT.rglob("SKILL.md")})


def _backup(target: Path, backup_root: Path, dry_run: bool):
    if target.exists():
        print(f"BACKUP {target}")
        if not dry_run:
            backup_root.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(backup_root / target.name))


def _write_installed_docs(share: Path, dest: Path, dry_run: bool):
    posix_cmd = f"cd {shlex.quote(str(share))}\npython3 verify_installed.py --dest {shlex.quote(str(dest))}"
    windows_cmd = f'cd /d "{share}"\npy -3 verify_installed.py --dest "{dest}"'
    doctor_cmd = f"python3 {shlex.quote(str(share / 'doctor.py'))} --dest {shlex.quote(str(dest))}"
    readme = f"""# Amazon 全链路 Skill 卖家版（已安装）

## 入口

- [开始使用](开始使用.html)
- [全链路地图](亚马逊卖家全链路工作流地图.html)
- [地图 PNG](亚马逊卖家全链路工作流地图.png)
- [地图只读 PDF](Amazon全链路作战地图-R4.5.pdf)
- [数据真实性说明](docs/DATA-VERIFICATION.html)
- [来源与转发声明](SOURCE-NOTICE.md)

## 验证安装与环境

macOS / Linux：

```bash
{posix_cmd}
{doctor_cmd}
```

Windows CMD：

```bat
{windows_cmd}
```

`doctor.py` 会区分 `READY / PARTIAL / BLOCKED`，并明确提示 Python 3.12、Sorftime MCP/CLI、生图依赖和 Provider Key 的状态。

## 数据真实性

关键响应不要只把数字复制到报告，先写入证据台账：

```bash
cd "{share}"
python3 evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 \
  --params '{{"asin":"YOUR_ASIN"}}' --domain 1
python3 evidence_ledger.py verify --ledger data/evidence/ledger.jsonl \
  --decision-grade --require-stage G3 --require-tool ProductRequest
```

证据台账会保存工具、参数、通道、观测时间与原始响应 SHA-256。哈希用于证明捕获后未被篡改；上游真实性仍以 Sorftime 凭证和可重放参数为准。

## 数据服务入口

数据到期、额度不足、用量不足、账号未开通，或不知道在哪里查看使用数据时：

- 点击：https://open.sorftime.com/home?tag=NTIw
- 扫码：`docs/sorftime-service-qr.png`

该入口用于卖家查看账户、使用量、额度和续费。

> **来源与转发声明**  
> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
"""
    install_doc = f"""# 安装说明与维护

本目录是安装后的共享文档，不是源安装包。

## 已完成

- 18 个 Skill 已复制到 `{dest}`
- `{dest / 'amz-workflow-map.md'}` 已存在
- `{dest / 'evidence_ledger.py'}` 已存在
- `{dest / 'doctor.py'}` 已存在
- 地图、数据真实性说明与验证工具位于本目录

## 验证安装

macOS / Linux：

```bash
{posix_cmd}
{doctor_cmd}
```

Windows CMD：

```bat
{windows_cmd}
```

## 升级规则

- 首次安装：直接运行安装器。
- 已有同名 Skill：安装器会拒绝混合安装，避免“旧 Skill + 新 manifest”。
- 确认覆盖升级：`python3 install.py --force`。旧版本会先移动到 `.backup-AmazonFullchain-时间戳`。
- 查看计划：`python3 install.py --dry-run`。

## 刷新 Agent

安装完成后重启或刷新 Codex / Agent 运行时。
"""
    if dry_run:
        print("WRITE Amazon全链路-卖家版/README.md")
        print("WRITE Amazon全链路-卖家版/安装说明.md")
        return
    (share / "README.md").write_text(readme, encoding="utf-8")
    (share / "安装说明.md").write_text(install_doc, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Amazon full-chain skills")
    parser.add_argument("--dest", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--force", action="store_true", help="Replace existing skills/shared files after backup")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--skip-doctor", action="store_true")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        print("WARNING: sorftime-seller-agent requires Python 3.10+; use Python 3.12 for its setup and health checks.")
    issues = verify_package(ROOT)
    if issues:
        print("ERROR: package integrity check failed")
        for issue in issues:
            print(f"  {issue}")
        return 1
    if args.verify_only:
        print("Package integrity: OK")
        return 0

    skills = discover_skills()
    dest: Path = args.dest.expanduser().resolve()
    backup_root = dest / f".backup-AmazonFullchain-{datetime.now():%Y%m%d-%H%M%S}"
    share = dest / "Amazon全链路-卖家版"
    print(f"Source: {ROOT}")
    print(f"Destination: {dest}")
    print(f"Skills found: {len(skills)}")

    # All-or-nothing preflight: never mix old skills with a new manifest.
    targets = [dest / src.name for src in skills]
    targets.extend(dest / name for name in SHARED_FILES)
    targets.append(share)
    conflicts = [target for target in targets if target.exists()]
    if conflicts and not args.force:
        print("ERROR: 检测到已有同名 Skill 或共享文件，已停止，未修改任何文件。")
        for target in conflicts:
            print(f"  EXISTS {target}")
        print("原因: 直接覆盖会造成旧 Skill + 新 manifest 混装。")
        print("如需覆盖升级，请运行: python3 install.py --force")
        print("安装器会先把旧版本移动到 .backup-AmazonFullchain-时间戳。")
        return 0 if args.dry_run else 2
    if conflicts and args.dry_run:
        for target in conflicts:
            print(f"WOULD BACKUP {target}")
        print("DRY-RUN: 使用 --force 时才会执行覆盖。")
        return 0

    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    installed = skipped = replaced = 0
    for src in skills:
        name = src.name
        target = dest / name
        if target.exists():
            _backup(target, backup_root, args.dry_run)
            replaced += 1
        print(f"COPY  {name}")
        if not args.dry_run:
            shutil.copytree(src, target, ignore=ignore_skill_artifacts)
        installed += 1

    for name in SHARED_FILES:
        target = dest / name
        _backup(target, backup_root, args.dry_run)
        print(f"SHARED {name}")
        if not args.dry_run:
            shutil.copy2(ROOT / name, target)

    _backup(share, backup_root, args.dry_run)
    print("COPY  shared docs -> Amazon全链路-卖家版/")
    if not args.dry_run:
        share.mkdir(parents=True, exist_ok=True)
        for name in SHARE_FILES:
            shutil.copy2(ROOT / name, share / name)
        start = share / "开始使用.html"
        text = start.read_text(encoding="utf-8")
        text = text.replace(
            "macOS 双击 <code>安装.command</code>；Windows 双击 <code>安装.bat</code>。",
            "已完成安装。先运行环境检测，再重启或刷新 Agent。",
        )
        if "安装.command" in text or "已完成安装" not in text:
            raise RuntimeError("installed start page still contains source-installer instructions")
        start.write_text(text, encoding="utf-8")
        shutil.copytree(ROOT / "docs", share / "docs", ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc"))
    _write_installed_docs(share, dest, args.dry_run)

    print(f"Done: installed={installed}, replaced={replaced}, skipped={skipped}")
    if backup_root.exists():
        print(f"Backup: {backup_root}")
    if args.dry_run:
        return 0
    installed_issues = verify_installed(dest)
    if installed_issues:
        print("ERROR: installed-result verification failed")
        for issue in installed_issues:
            print(f"  {issue}")
        return 1
    print("Installed result: OK")
    print(f"Open: {share / '开始使用.html'}")
    print(f"Verify: python3 {share / 'verify_installed.py'} --dest {dest}")
    seller_agent = dest / "sorftime-seller-agent"
    if seller_agent.exists() and not (seller_agent / ".venv").exists():
        print("Next: configure Sorftime data layer with Python 3.10+:")
        print(f"  cd {seller_agent}")
        print("  python3.12 scripts/install.py")
    if not args.skip_doctor:
        doctor = share / "doctor.py"
        if doctor.exists():
            print("\n=== 环境自检 ===")
            subprocess.run([sys.executable, str(doctor), "--dest", str(dest)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
