# AntSkill Creator

A structured production system for moving a skill from requirements to a deliverable package.

[![X](https://img.shields.io/badge/Follow-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

English | [简体中文](README.zh.md)

---

## Core mechanisms

| Mechanism | Purpose | File |
|------|------|----------|
| Paradigm classification | Distinguishes implementation-first (A), spec-first (B), and dual-mode (C) skills, each with a different workflow | `methodology/paradigms.md` |
| S1–S6 stage gates | Requirements → prototype → refinement → PRD → delivery → review, each with entry and exit criteria | `sop/`, `quality/gates.md` |
| 4-layer pipeline | Separates data, compute, decision, and rendering to avoid logic coupling | `prompts/layer_design_guides.md` |
| Source-of-truth arbitration | Defines precedence when PRD, API spec, prompts, and demo conflict | `methodology/source-of-truth.md` |
| Production / Prototype boundary | Separates visual reference from production contract | `methodology/responsibility-split.md` |

## Repository facts

| Metric | Value |
|------|------|
| Skill paradigms | 3 |
| SOP stages | 6 |
| Methodology modules | 4 |
| Reference templates | 10 |
| Built-in example packages | 4 |
| Yield Desk PRD | 1060 lines |
| DualYield tests | 32/32 passed |
| Yield Desk tests | 16/16 passed |

## What changed in the standard

This version makes two things explicit:

1. **Every serious skill must have a product PRD** that explains the complete product logic, not just scattered specs.
2. **Requirement docs and implementation artifacts must be physically separated** so a reviewer can tell at a glance whether a package is spec-first, implementation-first, or dual-mode.

## Standard package topology

```text
skill-name/
├── docs/                     # requirement-facing artifacts
│   ├── product/PRD.md        # complete product logic (mandatory for B/C)
│   ├── requirements/         # business/API/compute/prompt/viz/test specs
│   ├── review/               # review and gap reports
│   └── handoff/              # optional engineering handoff docs
├── implementation/           # runtime-facing artifacts
│   ├── pipeline/
│   ├── frontend/
│   ├── tests/
│   └── scripts/
├── delivery/                 # publish-facing artifacts
│   ├── SKILL.md
│   ├── README.md
│   ├── README.zh.md
│   ├── VERSION
│   ├── agents/openai.yaml
│   └── assets/
└── examples/                 # optional reference packages
```

## Repository structure

```text
antskill-creator/
├── SKILL.md                  # orchestration logic and decision tree
├── docs/                     # index + product PRD + package standard + guides
├── methodology/              # paradigms, SoT, responsibility split
├── sop/                      # S1–S6 stage playbooks
├── prompts/                  # L1–L4 design guides
├── quality/                  # gates and evaluation rules
├── templates/                # templates, skeletons, validators
└── examples/                 # full example packages
```

## Start here

- Docs index: `docs/INDEX.md`
- Quickstart: `docs/guides/quickstart.md`
- Package standard: `docs/standards/package-standard.md`
- Migration guide: `docs/guides/migration-guide.md`
- Example authoring guide: `docs/guides/example-authoring-guide.md`
- Example packages: `examples/README.md`

## Cases

### DualYield — C paradigm (dual-mode)

Includes product spec, pipeline code, frontend prototype, tests, and technical onboarding docs. L2 tests pass 32/32.

Path: `examples/dualyield/`

### Yield Desk — C paradigm (handoff-heavy)

Includes a 1060-line layered PRD, high-fidelity frontend prototype, and engineering handoff docs. L2 tests pass 16/16.

Path: `examples/yield-desk/`

### SeerClaw Ref — B paradigm (spec-first)

A pure reference package for scanner/analyzer-style product specs.

Path: `examples/seerclaw-ref/`

## Output types

| Paradigm | Output |
|------|------|
| A — Implementation-first | pipeline code, tests, frontend demo |
| B — Spec-first | spec docs, `SKILL.md`, frontend demo, metadata |
| C — Dual-mode | A + B |

## Usage

```text
/antskill-creator create a skill for on-chain treasury monitoring
/antskill-creator split this large skill into scanner and analyzer
/antskill-creator package this PRD + prototype into a GitHub-shareable skill
/antskill-creator review this skill and produce a gap report before handoff
```

Internal flow: classify paradigm → collect requirements → prototype → refine → PRD/spec → package + review.

## Best fit

**Good for:** skill production that needs both product clarity and engineering implementability; teams that need end-to-end demo/PRD/package/review management; reusable skill methodology.

**Not good for:** throwaway one-off skills; personal experiments that do not need review or packaging discipline.

---

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents
