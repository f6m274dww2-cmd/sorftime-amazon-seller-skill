#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify source package and re-export installed-result verification."""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from verify_installed import INSTALLED_REQUIRED, EXPECTED_SKILLS, verify_installed

ROOT = Path(__file__).resolve().parent

EXCLUDE_PARTS = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_NAMES = {".DS_Store"}
EXCLUDE_MARKERS = (".bak", " 2")


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

ROOT_REQUIRED = {
    "README.md", "安装说明.md", "开始使用.html", "amz-workflow-map.md",
    "亚马逊卖家全链路工作流地图.html", "亚马逊卖家全链路工作流地图.png",
    "Amazon全链路作战地图-R4.5.pdf", "SOURCE-NOTICE.md", "CHECKSUMS.sha256",
    "Sorftime-CHANNEL.md", "verify_package.py", "verify_installed.py",
    "install.py", "安装.command", "安装.bat", "manifest.json",
    "doctor.py", "evidence_ledger.py", "requirements-image.txt",
    "THIRD-PARTY-NOTICES.md", "docs/DATA-VERIFICATION.html",
    "docs/sorftime-service-qr.png", "docs/sorftime-jennifer-wecom-qr.png", "docs/FIX-REPORT.html", "RELEASE-NOTES.md",
}

SOURCE_TEXT = (
    "本 Skill 及配套作战地图由 Sorftime Jennifer 提供。"
    "允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。"
)
SOURCE_VISIBLE_FILES = (
    "README.md", "安装说明.md", "amz-workflow-map.md", "开始使用.html",
    "亚马逊卖家全链路工作流地图.html", "SOURCE-NOTICE.md", "Sorftime-CHANNEL.md",
)


def _scan_markdown_links(path: Path, root: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        link = match.group(1)
        if "://" in link or link.startswith(("#", "mailto:", "data:", "/")) or "*" in link:
            continue
        target = (path.parent / link.split("#")[0]).resolve()
        if not target.exists():
            yield {"type": "missing_relative_file", "source": str(path.relative_to(root)), "target": link}


class _HTMLRefs(HTMLParser):
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


def verify_package(root: Path = ROOT) -> list[dict]:
    issues: list[dict] = []
    for name in sorted(ROOT_REQUIRED):
        if not (root / name).exists():
            issues.append({"type": "missing_root_file", "path": name})
    if not (root / "docs").is_dir():
        issues.append({"type": "missing_root_dir", "path": "docs"})

    skills = sorted({p.parent for p in (root / "skills").rglob("SKILL.md")})
    found_names = {p.name for p in skills}
    for name in sorted(EXPECTED_SKILLS - found_names):
        issues.append({"type": "missing_skill", "skill": name})
    for name in sorted(found_names - EXPECTED_SKILLS):
        issues.append({"type": "unexpected_skill", "skill": name})

    for skill in skills:
        text = (skill / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
        if SOURCE_TEXT not in text:
            issues.append({"type": "missing_source_notice", "skill": skill.name})
        if "NTIw" not in text and not (skill / "Sorftime-CHANNEL.md").exists():
            issues.append({"type": "missing_sorftime_tag", "skill": skill.name})
        if "~/.agents/skills/" in text:
            issues.append({"type": "hardcoded_skills_path", "skill": skill.name})
        for md in skill.rglob("*.md"):
            issues.extend(_scan_markdown_links(md, root))

    root_docs = [root / n for n in ("README.md", "安装说明.md") if (root / n).exists()]
    root_docs += list((root / "docs").rglob("*.md")) if (root / "docs").exists() else []
    for md in root_docs:
        issues.extend(_scan_markdown_links(md, root))
        if "全链路地图.png" in md.read_text(encoding="utf-8", errors="ignore"):
            issues.append({"type": "stale_map_filename", "source": str(md.relative_to(root))})
    root_html = [root / "开始使用.html", root / "亚马逊卖家全链路工作流地图.html"]
    root_html += list((root / "docs").rglob("*.html")) if (root / "docs").exists() else []
    for html in root_html:
        if not html.exists():
            continue
        parser = _HTMLRefs(); parser.feed(html.read_text(encoding="utf-8", errors="ignore"))
        for ref in parser.refs:
            if "://" in ref or ref.startswith(("#", "mailto:", "data:", "/")):
                continue
            if not (html.parent / ref.split("#")[0]).exists():
                issues.append({"type": "missing_html_ref", "source": str(html.relative_to(root)), "target": ref})

    for name in SOURCE_VISIBLE_FILES:
        path = root / name
        if path.exists() and SOURCE_TEXT not in path.read_text(encoding="utf-8", errors="ignore"):
            issues.append({"type": "missing_source_notice", "path": name})

    checksums_path = root / "CHECKSUMS.sha256"
    if checksums_path.exists():
        import hashlib
        for line_no, line in enumerate(checksums_path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                expected, rel = line.split("\t", 1)
            except ValueError:
                issues.append({"type": "invalid_checksum_line", "line": line_no})
                continue
            target = (root / rel).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                issues.append({"type": "checksum_path_escape", "path": rel})
                continue
            if not target.is_file():
                issues.append({"type": "checksum_missing_file", "path": rel})
            elif hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                issues.append({"type": "checksum_mismatch", "path": rel})

    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        import hashlib
        import json
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_skills = set(manifest.get("skills", {}))
            if manifest_skills != EXPECTED_SKILLS:
                issues.append({"type": "manifest_skill_set_mismatch", "missing": sorted(EXPECTED_SKILLS - manifest_skills), "unexpected": sorted(manifest_skills - EXPECTED_SKILLS)})
            for skill, meta in manifest.get("skills", {}).items():
                skill_dir = root / meta.get("path", "")
                if not (skill_dir / "SKILL.md").exists():
                    issues.append({"type": "manifest_missing_skill", "skill": skill})
                    continue
                actual, count = _tree_digest(skill_dir)
                if actual != meta.get("tree_sha256") or count != meta.get("file_count"):
                    issues.append({"type": "manifest_hash_mismatch", "skill": skill, "actual_files": count, "expected_files": meta.get("file_count")})
            for rel, expected in manifest.get("artifacts", {}).items():
                target = (root / rel).resolve()
                try:
                    target.relative_to(root.resolve())
                except ValueError:
                    issues.append({"type": "manifest_artifact_path_escape", "path": rel})
                    continue
                if not target.is_file():
                    issues.append({"type": "manifest_artifact_missing", "path": rel})
                elif hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                    issues.append({"type": "manifest_artifact_mismatch", "path": rel})
        except Exception as exc:
            issues.append({"type": "invalid_manifest", "error": str(exc)})
    return issues


if __name__ == "__main__":
    problems = verify_package()
    count = len(sorted({p.parent for p in (ROOT / "skills").rglob("SKILL.md")}))
    print(f"skills={count} issues={len(problems)}")
    for problem in problems:
        print(problem)
    raise SystemExit(1 if problems else 0)
