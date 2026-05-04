#!/usr/bin/env python3
"""Create a distributable .skill archive after two-stage validation.

Usage:
    python package_skill.py <skill-folder> [output-directory] [--stage auto|requirement|complete] [--run-checks]
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_shareable_skill import validate_package  # noqa: E402

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", ".venv"}
EXCLUDE_GLOBS = {"*.pyc", "*.skill"}
EXCLUDE_FILES = {".DS_Store"}


def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if rel_path.name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(rel_path.name, pat) for pat in EXCLUDE_GLOBS)


def package_skill(skill_path: Path, output_dir: Path | None, stage: str, run_checks: bool) -> Path | None:
    skill_path = skill_path.resolve()
    if not skill_path.exists() or not skill_path.is_dir():
        print(f"❌ Skill folder not found: {skill_path}")
        return None

    print("🔍 Validating skill package...")
    report = validate_package(skill_path, stage=stage, run_checks=run_checks)
    if not report.ok:
        print(f"❌ Validation failed for stage: {report.stage}\n")
        for error in report.errors:
            print(f"- {error}")
        if report.warnings:
            print("\nWarnings:\n")
            for warning in report.warnings:
                print(f"- {warning}")
        return None
    print(f"✅ Valid for stage: {report.stage}")
    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"- {warning}")
    print()

    output_path = output_dir.resolve() if output_dir else skill_path.parent
    output_path.mkdir(parents=True, exist_ok=True)
    archive_path = output_path / f"{skill_path.name}.skill"
    if archive_path.exists():
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in skill_path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.resolve() == archive_path.resolve():
                print(f"  Skipped archive itself: {file_path}")
                continue
            arcname = file_path.relative_to(skill_path.parent)
            if should_exclude(arcname):
                print(f"  Skipped: {arcname}")
                continue
            zipf.write(file_path, arcname)
            print(f"  Added: {arcname}")

    print(f"\n✅ Packaged skill to: {archive_path}")
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_path")
    parser.add_argument("output_dir", nargs="?")
    parser.add_argument("--stage", choices=["auto", "requirement", "complete"], default="auto")
    parser.add_argument("--run-checks", action="store_true")
    args = parser.parse_args()

    result = package_skill(
        Path(args.skill_path),
        Path(args.output_dir) if args.output_dir else None,
        args.stage,
        args.run_checks,
    )
    return 0 if result else 1


if __name__ == "__main__":
    raise SystemExit(main())
