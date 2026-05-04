# Skill Publishing Standard

This reference defines where created or upgraded Stage 1 / Stage 2 skills are published after they pass the relevant stage gates.

## Repository ownership

| Repository | Purpose | URL |
|---|---|---|
| Creator repository | Maintains and releases `skill-creator-rick` itself | `https://github.com/antseer/skill-creator-rick` |
| Generated skill publish repository | Publishes Stage 1 / Stage 2 skills produced by the creator | `https://github.com/antseer/test_skills` |

Do not mix these responsibilities: updates to this creator package are committed to `antseer/skill-creator-rick`; generated skills are copied into `antseer/test_skills` after validation.

## Canonical generated-skill publish repository

- Local publish directory: `/Users/rick/code/job/external/test_skills`
- Git remote: `https://github.com/antseer/test_skills.git`
- Branch: `main`

Treat this repository as the default publishing target for future Antseer/Rick Stage 1 / Stage 2 skills unless the user explicitly names another target. The local checkout must have this remote; do not use `/Users/rick/code/job/skills_rick` unless its remote is explicitly changed to `https://github.com/antseer/test_skills.git`.

## Directory layout

Publish one skill per top-level directory:

```text
/Users/rick/code/job/external/test_skills/
├── README.md
├── <skill-slug>/
│   ├── SKILL.md
│   ├── README.md
│   ├── README.zh.md
│   ├── skill.meta.json
│   ├── VERSION
│   └── ...stage-specific files
```

Rules:

1. Use a stable kebab-case slug for the top-level directory.
2. Do not publish directly into `~/.claude/skills`, `~/.codex/skills`, or `~/.cursor/skills`; `~/.claude/skills` is the personal source-of-truth/install location, while Codex/Cursor paths are local mirrors. None of them is the shared publishing repo.
3. Do not mix multiple independent skills in one top-level directory.
4. Do not commit generated junk: `.DS_Store`, `__pycache__`, `*.pyc`, `.skill`, temporary zips, local caches, component checkouts, `node_modules`, or secrets.
5. If the publish repo already contains a related skill, inspect its layout and metadata before adding a new one so naming, README structure, icons, `skill.meta.json`, and release notes stay consistent.
6. Never overwrite or clean unrelated changes in the publish repo. If `git status` is dirty before publishing, report it and only touch the target skill directory plus repo index files that must change.

## Publish workflow

When the user asks to publish a generated Stage 1 / Stage 2 skill:

1. Validate the source skill with the proper Stage 1 / Stage 2 gate.
2. Run required frontend SoT and sub-agent review gates if the package contains Antseer frontend, is Stage 2, or is being released.
3. Inspect `/Users/rick/code/job/external/test_skills`:
   - confirm it is a git repo with remote `https://github.com/antseer/test_skills.git`;
   - confirm the current branch is `main` before commit/push;
   - list existing top-level skills for naming/style reference;
   - check `git status --short` and protect unrelated changes.
4. Copy/sync only the validated skill package into `/Users/rick/code/job/external/test_skills/<skill-slug>/`.
5. Update the publish repo README/index if it lists available skills.
6. Re-run package validation from the published directory.
7. Commit and push to the publish repo only after validation passes and required review gates are clean.
8. Report the published path, commit, branch, remote URL, stage, validation summary, and any remaining non-blocking P2/P3 items.

## Reference-first writing

Before shaping a new published skill, prefer local references in this order:

1. Existing related skill under `/Users/rick/code/job/external/test_skills/<skill-slug>/`.
2. This skill package's templates and standards under `templates/` and `references/`.
3. `antseer-components` frontend standard for any frontend/UI artifact.
4. MCP capability map and `MCP-COVERAGE.md` pattern for real data/source coverage.

Reference existing skills for style only; do not inherit their stale mock data, secrets, deprecated structure, or unverified assumptions.
