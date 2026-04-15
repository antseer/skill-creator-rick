# AntSkill Creator — Quickstart

> Updated: 2026-04-15

## What this repo does

AntSkill Creator helps turn a skill idea into a package that is:

- product-clear
- implementation-readable
- publish-ready

The core rule is simple:

- `docs/` = requirements
- `implementation/` = runtime
- `delivery/` = publish surface

## If you only have 3 minutes

Read these in order:

1. `docs/standards/package-standard.md`
2. `examples/README.md`
3. one example package that matches your need

## Pick your path

### Path 1 — I want to migrate an old package

Read:

1. `docs/standards/package-standard.md`
2. `docs/guides/migration-guide.md`
3. `examples/README.md`

Then do:

1. decide A / B / C
2. move PRD to `docs/product/PRD.md`
3. split files into `docs/`, `implementation/`, `delivery/`
4. fix all path references

### Path 2 — I want to create a new example

Read:

1. `docs/standards/package-standard.md`
2. `docs/guides/example-authoring-guide.md`
3. `examples/README.md`

Then do:

1. choose the teaching objective
2. choose A / B / C
3. write `docs/product/PRD.md`
4. add only the minimum implementation needed
5. write `delivery/README.md` and `delivery/SKILL.md` last

### Path 3 — I just want a good reference

Use:

- `examples/dualyield/` for a full C dual-mode example
- `examples/yield-desk/` for a PRD-heavy C example
- `examples/seerclaw-ref/` for a B spec-first example
- `examples/yield-desk-ref/` for a small A implementation reference

## Rules you should memorize

1. every serious package needs one clear PRD
2. requirement docs and implementation files must not mix
3. `delivery/` is a facade, not product truth
4. README explains; docs define
5. if a reviewer cannot understand the package in 10 seconds, the structure is still wrong

## Minimal checklist

- [ ] package type A / B / C is explicit
- [ ] `docs/product/PRD.md` exists
- [ ] `docs/`, `implementation/`, `delivery/` are clearly separated
- [ ] README points to real files
- [ ] example choice or migration path is obvious

## Where to go next

- Full standard: `docs/standards/package-standard.md`
- Migration guide: `docs/guides/migration-guide.md`
- Example authoring guide: `docs/guides/example-authoring-guide.md`
- Example index: `examples/README.md`
