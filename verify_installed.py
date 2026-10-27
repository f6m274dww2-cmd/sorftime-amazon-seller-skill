#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify an installed Amazon full-chain skill directory."""
from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

EXPECTED_SKILLS = {
    "sorftime-seller-agent", "sorftime-data-cli",
    "amz-fullchain-jtbd", "amz-selection", "amz-market-analysis",
    "amz-supply-chain", "amz-profit-calc", "amz-cpc-keywords",
    "amz-listing-creator", "amz-image-creator", "amz-ad-planning",
    "amz-voc-analysis", "amz-competitor-monitor", "sorftime-patent-risk",
    "ecommerce-visual-copywriting", "product-shots-main-image",
    "product-shots-detail-page", "product-shots-image-gen",
}

EXCLUDE_PARTS = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_NAMES = {".DS_Store"}
EXCLUDE_MARKERS = (".bak", " 2")
SOURCE_TEXT = (
    "本 Skill 及配套作战地图由 Sorftime Jennifer 提供。"
    "允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。"
)


def _included(path: Path) -> bool:
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return False
    if path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES:
        return False
    return not any(marker in path.name for marker in EXCLUDE_MARKERS)


def _tree_digest(skill_dir: Path):
    import hashlib
    files = []
    for path in sorted(p for p in skill_dir.rglob("*") if p.is_file() and _included(p)):
        rel = path.relative_to(skill_dir).as_posix()
        files.append((rel, hashlib.sha256(path.read_bytes()).hexdigest()))
    material = "\n".join(f"{rel}\0{digest}" for rel, digest in files).encode()
    return hashlib.sha256(material).hexdigest(), len(files)

INSTALLED_REQUIRED = {
    "amz-workflow-map.md",
    "SOURCE-NOTICE.md",
    "Amazon全链路-卖家版/开始使用.html",
    "Amazon全链路-卖家版/亚马逊卖家全链路工作流地图.html",
    "Amazon全链路-卖家版/亚马逊卖家全链路工作流地图.png",
    "Amazon全链路-卖家版/Amazon全链路作战地图-R4.5.pdf",
    "Amazon全链路-卖家版/SOURCE-NOTICE.md",
    "Amazon全链路-卖家版/README.md",
    "Amazon全链路-卖家版/安装说明.md",
    "Amazon全链路-卖家版/Sorftime-CHANNEL.md",
    "Amazon全链路-卖家版/verify_installed.py",
    "Amazon全链路-卖家版/manifest.json",
    "Amazon全链路-卖家版/docs/FIX-REPORT.html",
    "Amazon全链路-卖家版/docs/DATA-VERIFICATION.html",
    "Amazon全链路-卖家版/docs/sorftime-service-qr.png",
    "Amazon全链路-卖家版/docs/sorftime-jennifer-wecom-qr.png",
    "Amazon全链路-卖家版/doctor.py",
    "Amazon全链路-卖家版/evidence_ledger.py",
    "Amazon全链路-卖家版/requirements-image.txt",
    "Amazon全链路-卖家版/THIRD-PARTY-NOTICES.md",
    "Amazon全链路-卖家版/RELEASE-NOTES.md",
    "doctor.py",
    "evidence_ledger.py",
    "requirements-image.txt",
    "THIRD-PARTY-NOTICES.md",
    "RELEASE-NOTES.md",
}


class _Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and d.get("href"):
            self.refs.append(d["href"])
        elif tag in {"img", "script", "link"}:
            value = d.get("src") or d.get("href")
            if value:
                self.refs.append(value)


def _scan_md(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        link = match.group(1)
        if "://" in link or link.startswith(("#", "mailto:", "data:", "/")) or "*" in link:
            continue
        if not (path.parent / link.split("#")[0]).exists():
            yield {"type": "installed_missing_md_ref", "source": str(path), "target": link}


def _scan_html(path: Path):
    parser = _Refs(); parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    for ref in parser.refs:
        if "://" in ref or ref.startswith(("#", "mailto:", "data:", "/")):
            continue
        if not (path.parent / ref.split("#")[0]).exists():
            yield {"type": "installed_missing_html_ref", "source": str(path), "target": ref}


def verify_installed(dest: Path) -> list[dict]:
    import hashlib
    import json

    dest = dest.expanduser().resolve()
    issues: list[dict] = []
    for rel in sorted(INSTALLED_REQUIRED):
        if not (dest / rel).exists():
            issues.append({"type": "missing_installed_file", "path": rel})
    for skill in sorted(EXPECTED_SKILLS):
        if not (dest / skill / "SKILL.md").exists():
            issues.append({"type": "missing_installed_skill", "skill": skill})
    share = dest / "Amazon全链路-卖家版"
    manifest_path = share / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_skills = set(manifest.get("skills", {}))
            if manifest_skills != EXPECTED_SKILLS:
                issues.append({
                    "type": "manifest_skill_set_mismatch",
                    "missing": sorted(EXPECTED_SKILLS - manifest_skills),
                    "unexpected": sorted(manifest_skills - EXPECTED_SKILLS),
                })
            for skill, meta in manifest.get("skills", {}).items():
                skill_dir = dest / skill
                if not (skill_dir / "SKILL.md").exists():
                    continue
                actual, count = _tree_digest(skill_dir)
                if actual != meta.get("tree_sha256") or count != meta.get("file_count"):
                    issues.append({"type": "installed_skill_version_mismatch", "skill": skill, "actual_files": count, "expected_files": meta.get("file_count")})
        except Exception as exc:
            issues.append({"type": "invalid_manifest", "error": str(exc)})
    if share.exists():
        for md in share.rglob("*.md"):
            issues.extend(_scan_md(md))
        for html in share.rglob("*.html"):
            issues.extend(_scan_html(html))
    # A custom --dest install must not retain the old default-path reference.
    for skill in sorted(EXPECTED_SKILLS):
        skill_md = dest / skill / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        if SOURCE_TEXT not in text:
            issues.append({"type": "installed_missing_source_notice", "skill": skill})
        if "~/.agents/skills/" in text:
            issues.append({"type": "installed_hardcoded_skills_path", "skill": skill})
    for rel in ("amz-workflow-map.md", "SOURCE-NOTICE.md", "Amazon全链路-卖家版/README.md", "Amazon全链路-卖家版/开始使用.html", "Amazon全链路-卖家版/亚马逊卖家全链路工作流地图.html"):
        path = dest / rel
        if path.exists() and SOURCE_TEXT not in path.read_text(encoding="utf-8", errors="ignore"):
            issues.append({"type": "installed_missing_source_notice", "path": rel})
    return issues


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dest", type=Path, default=Path.home() / ".agents" / "skills")
    args = p.parse_args()
    dest = args.dest.expanduser().resolve()
    issues = verify_installed(dest)
    print(f"destination={dest} issues={len(issues)}")
    for issue in issues:
        print(issue)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
