<div align="center">

# Skill Creator Rick

Move a skill through a two-stage lifecycle while preserving the original AntSkill Creator methodology and S0-S5 build pipeline.

English | [简体中文](README.zh.md)

</div>

## Two stages

### Stage 1 — Semi-finished Skill

Use this when the product plan is complete but real data integration is not finished.

Required outcome:
- full product plan / PRD / user flow
- frontend or output experience
- backend capability requirements
- data-source dependency list
- mock-data boundary and replacement plan
- engineering implementation docs

The skill may use mock data, but every mock item must map to the real MCP / API / database source that will replace it.

### Stage 2 — Finished Skill

Use this when the Stage 1 mock data has been replaced.

Required outcome:
- user path no longer depends on mock / stub / random demo data
- all required data dependencies are covered by MCP / API / database or explicitly marked as not requiring external data
- `MCP-COVERAGE.md` proves coverage
- README contains data sources and validation evidence
- package can be installed, run, shared, or published

> `split` is a packaging action, not a third stage.

## What this skill does

- classify a local skill as Stage 1 Semi-finished or Stage 2 Finished
- run the original S0-S5 creation pipeline from raw idea to handoff-ready skill package
- preserve methodology, SOP, quality gates, design-system rules, and MCP routing decisions
- detect when a mixed package should be split first
- scaffold stage-specific files from maintainable templates
- add bilingual README files, metadata, icons, and agent facade
- generate engineering-facing MCP / API / data-source request docs
- validate stage-specific package readiness
- generate structured audit reports with score, missing items, and Stage 2 blockers
- publish to GitHub when asked

## Pipeline and methodology

The lifecycle stage and the build pipeline are two different axes:

| Axis | Purpose |
|---|---|
| Stage 1 / Stage 2 | Tells the truth about package readiness and mock/data-source coverage |
| S0-S5 pipeline | Orchestrates how to create a skill from idea → inventory → MCP routing → PRD → UI → review → package |

Core restored assets:

| Asset | Purpose |
|---|---|
| `PIPELINE.md` | S0-S5 orchestration overview and relation to Stage 1 / Stage 2 |
| `STAGE-GATES.md` | Explicit pass / stop / split / publish gates for lifecycle and S0-S5 workflow |
| `methodology/` | core principles, intent anchoring, paradigms, responsibility split, semi-finished boundary, source of truth |
| `sop/` | step-by-step execution SOP for S0-S5 |
| `quality/` | G0-G5 quality gates |
| `mcp-capability-map/` | L1-A / L1-B / L2 / L3 / L4 / L5 routing decision tree |
| `design-system/` | Antseer visual rules and visual registry |

## Data Sources

This meta-skill does not require external market data. It operates on local skill files provided by the user.

| Data item | Real source | Method | Last verified | Failure handling |
|---|---|---|---|---|
| Skill package files | User local filesystem | Direct file read/write | 2026-04-27 | Report missing files and required fixes |
| Package standards | Local references in this skill | `references/*.md` | 2026-04-27 | Fall back to `SKILL.md` contract |
| Stage gates | Local gate docs | `STAGE-GATES.md`, `quality/*.md` | 2026-05-04 | Stop packaging if missing |
| Pipeline SOP | Local pipeline docs | `PIPELINE.md`, `sop/*.md`, `quality/*.md` | 2026-05-04 | Fall back to `SKILL.md` pipeline table |
| Methodology | Local methodology docs | `methodology/*.md` | 2026-05-04 | Report missing methodology and stop creator workflow |
| Validation rules | Local Python scripts | `scripts/quick_validate.py`, `scripts/validate_shareable_skill.py`, `scripts/audit_skill.py` | 2026-05-04 | Print validation errors and audit reports |
| Scaffold templates | Local template files | `templates/requirement`, `templates/complete`, `templates/common` | 2026-05-04 | Fail fast if a template is missing |
| Executable checks | Local check config | `validation.checks.json` | 2026-05-04 | Fail the Stage 2 `--run-checks` gate |
| Antseer frontend component standard | External GitHub repo + external local cache | `scripts/sync_antseer_components.sh` → `${XDG_CACHE_HOME:-~/.cache}/skill-creator-rick/antseer-components` | 2026-05-04 | Use existing cache with commit disclosed, or stop if no cache exists |

## Validation Evidence

| Check | Command / method | Result | Date |
|---|---|---|---|
| Frontmatter validation | `PYTHONDONTWRITEBYTECODE=1 python scripts/quick_validate.py .` | pass | 2026-05-04 |
| Stage validator syntax | `PYTHONDONTWRITEBYTECODE=1 python -m py_compile scripts/*.py` | pass | 2026-05-04 |
| Raw Stage 1 scaffold guard | generate temp requirement package and confirm validation fails until placeholders are filled | pass | 2026-05-04 |
| Stage 2 scaffold smoke test | raw complete scaffold intentionally fails until placeholders are filled; filled fixture passes | pass with filled sample values | 2026-05-04 |
| Executable validation gate | `PYTHONDONTWRITEBYTECODE=1 python scripts/validate_shareable_skill.py . --stage complete --run-checks` | pass | 2026-05-04 |
| Structured audit report | `PYTHONDONTWRITEBYTECODE=1 python scripts/audit_skill.py . --stage complete --run-checks --format json` | pass | 2026-05-04 |
| Release boundary check | Confirm component checkout, `.git`, `node_modules`, pycache, and generated caches are absent from package source | pass | 2026-05-04 |

## Example requests

```text
/skill-creator-rick review this skill and tell me which stage it is
/skill-creator-rick scaffold a Stage 1 Semi-finished Skill from this PRD + prototype
/skill-creator-rick upgrade this Stage 1 package to Stage 2 after MCP is ready
/skill-creator-rick validate this package as Stage 2 Finished
/skill-creator-rick split this large skill into independent packages
```
