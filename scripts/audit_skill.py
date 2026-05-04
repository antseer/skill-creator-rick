#!/usr/bin/env python3
"""Generate a structured AntSkill two-stage audit report."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Keep audit runs from creating __pycache__ in packages that are immediately
# checked by the hygiene gate.
sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_shareable_skill import (  # noqa: E402
    COMPLETE_REQUIRED_FILES,
    COMMON_REQUIRED_FILES,
    REQUIREMENT_REQUIRED_FILES,
    contains_heading,
    detect_stage,
    find_product_plan_artifacts,
    frontend_files,
    has_junk,
    maybe_warn_missing_input_schema,
    read_text,
    scan_user_path_mocks,
    validate_frontend_sot,
    validate_complete,
    validate_input_schema,
    validate_package,
    validate_requirement,
)


@dataclass
class Dimension:
    name: str
    score: float
    passed: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class AuditReport:
    skill_path: str
    stage: str
    score: float
    verdict: str
    dimensions: list[Dimension]
    missing: list[str]
    warnings: list[str]
    stage2_blockers: list[str]
    validation_errors: list[str]


def exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def ratio(passed: int, total: int) -> float:
    if total <= 0:
        return 1.0
    return round(passed / total, 4)


def score_dimension(name: str, checks: list[tuple[str, bool]], warnings: list[str] | None = None) -> Dimension:
    passed = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    return Dimension(name=name, score=ratio(len(passed), len(checks)), passed=passed, missing=missing, warnings=warnings or [])


def common_dimensions(root: Path) -> list[Dimension]:
    dims: list[Dimension] = []
    frontmatter_report = validate_package(root, stage="auto", run_checks=False)
    frontmatter_errors = [e for e in frontmatter_report.errors if "frontmatter" in e.lower() or "SKILL.md" in e or "Name" in e or "Description" in e]
    dims.append(score_dimension("core_files", [(rel, exists(root, rel)) for rel in COMMON_REQUIRED_FILES]))
    dims.append(score_dimension("frontmatter", [("SKILL.md frontmatter valid", not frontmatter_errors)]))
    dims.append(score_dimension("hygiene", [("no junk files", not has_junk(root))]))
    schema_errors = validate_input_schema(root)
    schema_warnings = maybe_warn_missing_input_schema(root)
    dims.append(score_dimension("input_schema", [("input_schema valid or not required", not schema_errors)], schema_warnings))
    return dims


def requirement_dimensions(root: Path) -> list[Dimension]:
    readme = read_text(root / "README.md")
    readme_zh = read_text(root / "README.zh.md")
    tech_request = read_text(root / "TECH-INTERFACE-REQUEST.md")
    frontend_errors, frontend_warnings = validate_frontend_sot(root, "requirement")
    dims = [
        score_dimension("stage1_required_files", [(rel, exists(root, rel)) for rel in REQUIREMENT_REQUIRED_FILES]),
        score_dimension("data_reality", [
            ("README.md has Data Reality", contains_heading(readme, ["Data Reality"])),
            ("README.zh.md has 数据真实性", contains_heading(readme_zh, ["数据真实性"])),
        ]),
        score_dimension("product_plan", [
            ("product plan artifact exists", bool(find_product_plan_artifacts(root))),
        ]),
        score_dimension("tech_interface_request", [
            ("TECH-INTERFACE-REQUEST.md exists", exists(root, "TECH-INTERFACE-REQUEST.md")),
            ("mentions MCP/API/data/schema", any(term in tech_request.lower() for term in ["mcp", "api", "接口", "数据", "schema"])),
        ]),
    ]
    if frontend_files(root) or exists(root, "frontend"):
        dims.append(score_dimension("frontend_sot_best_effort", [
            ("no hard frontend SoT errors", not frontend_errors),
        ], frontend_warnings))
    return dims


def complete_dimensions(root: Path, run_checks: bool, run_errors: list[str] | None = None) -> list[Dimension]:
    readme = read_text(root / "README.md")
    readme_zh = read_text(root / "README.zh.md")
    coverage = read_text(root / "MCP-COVERAGE.md")
    validation_blob = readme + "\n" + readme_zh + "\n" + coverage
    run_errors = run_errors or []
    frontend_errors, frontend_warnings = validate_frontend_sot(root, "complete")
    dims = [
        score_dimension("stage2_required_files", [(rel, exists(root, rel)) for rel in COMPLETE_REQUIRED_FILES]),
        score_dimension("data_sources", [
            ("README.md has Data Sources", contains_heading(readme, ["Data Sources"])),
            ("README.zh.md has 数据来源", contains_heading(readme_zh, ["数据来源"])),
        ]),
        score_dimension("validation_evidence", [
            ("README.md has Validation Evidence", contains_heading(readme, ["Validation Evidence"])),
            ("README.zh.md has 验证证据", contains_heading(readme_zh, ["验证证据"])),
            ("MCP-COVERAGE.md has verification status", any(term in coverage.lower() for term in ["verified", "pass", "covered", "验证", "已覆盖", "通过"])),
        ]),
        score_dimension("mock_free_user_path", [
            ("no user-path mock/stub/random data detected", not scan_user_path_mocks(root)),
        ]),
        score_dimension("resolved_docs", [
            ("README/MCP-COVERAGE contain no TODO/待补", "TODO" not in validation_blob and "待补" not in validation_blob),
        ]),
    ]
    if frontend_files(root) or exists(root, "frontend"):
        dims.append(score_dimension("frontend_sot_hard_gate", [
            ("frontend passes antseer-components SoT gate", not frontend_errors),
        ], frontend_warnings))
    if run_checks:
        dims.append(score_dimension("executable_checks", [("validation.checks.json commands pass", not run_errors)]))
    return dims


def flatten_missing(dimensions: list[Dimension]) -> list[str]:
    out: list[str] = []
    for dim in dimensions:
        for item in dim.missing:
            out.append(f"{dim.name}: {item}")
    return out


def flatten_warnings(dimensions: list[Dimension]) -> list[str]:
    out: list[str] = []
    for dim in dimensions:
        for item in dim.warnings:
            out.append(f"{dim.name}: {item}")
    return out


def stage2_blockers(root: Path, stage: str, validation_errors: list[str], dimensions: list[Dimension]) -> list[str]:
    blockers: list[str] = []
    if stage == "requirement":
        blockers.extend(flatten_missing(dimensions))
        blockers.append("Stage 1 package has not proven real MCP/API/database coverage yet")
        return blockers
    for error in validation_errors:
        if any(key in error for key in ["Stage 2", "MCP-COVERAGE", "mock", "Data Sources", "Validation Evidence", "Run check", "frontend SoT"]):
            blockers.append(error)
    return blockers


def compute_verdict(stage: str, score: float, validation_errors: list[str], blockers: list[str]) -> str:
    if validation_errors:
        return "fail"
    if stage == "complete" and blockers:
        return "blocked"
    if score >= 0.95:
        return "share-ready"
    if score >= 0.75:
        return "needs-minor-work"
    return "needs-major-work"


def audit(root: Path, stage_arg: str, run_checks: bool) -> AuditReport:
    stage = detect_stage(root) if stage_arg == "auto" else stage_arg
    validation = validate_package(root, stage=stage, run_checks=run_checks)
    errors = validation.errors
    dims = common_dimensions(root)
    if stage == "requirement":
        dims.extend(requirement_dimensions(root))
    else:
        run_errors = [e for e in errors if e.startswith("Run check") or "validation.checks.json" in e]
        dims.extend(complete_dimensions(root, run_checks=run_checks, run_errors=run_errors))

    warnings = validation.warnings + flatten_warnings(dims)
    missing = flatten_missing(dims)
    score = round(sum(dim.score for dim in dims) / len(dims), 4) if dims else 0.0
    blockers = stage2_blockers(root, stage, errors, dims)
    verdict = compute_verdict(stage, score, errors, blockers)
    return AuditReport(
        skill_path=str(root),
        stage=stage,
        score=score,
        verdict=verdict,
        dimensions=dims,
        missing=missing,
        warnings=sorted(set(warnings)),
        stage2_blockers=sorted(set(blockers)),
        validation_errors=errors,
    )


def print_markdown(report: AuditReport) -> None:
    print(f"# Skill Creator Rick Audit Report\n")
    print(f"- Path: `{report.skill_path}`")
    print(f"- Stage: **{report.stage}**")
    print(f"- Score: **{report.score:.2%}**")
    print(f"- Verdict: **{report.verdict}**\n")

    print("## Dimensions\n")
    print("| Dimension | Score | Missing | Warnings |")
    print("|---|---:|---|---|")
    for dim in report.dimensions:
        missing = "<br>".join(dim.missing) if dim.missing else "—"
        warnings = "<br>".join(dim.warnings) if dim.warnings else "—"
        print(f"| {dim.name} | {dim.score:.0%} | {missing} | {warnings} |")

    if report.stage2_blockers:
        print("\n## Stage 2 Blockers\n")
        for item in report.stage2_blockers:
            print(f"- {item}")

    if report.validation_errors:
        print("\n## Validation Errors\n")
        for item in report.validation_errors:
            print(f"- {item}")

    if report.warnings:
        print("\n## Warnings\n")
        for item in report.warnings:
            print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_path")
    parser.add_argument("--stage", choices=["auto", "requirement", "complete"], default="auto")
    parser.add_argument("--run-checks", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = audit(Path(args.skill_path).resolve(), args.stage, args.run_checks)
    if args.format == "json":
        text = json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"
    else:
        from io import StringIO
        old_stdout = sys.stdout
        buf = StringIO()
        try:
            sys.stdout = buf
            print_markdown(report)
        finally:
            sys.stdout = old_stdout
        text = buf.getvalue()

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if not report.validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
