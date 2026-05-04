# Skill Creator Rick · MCP Coverage

This meta-skill does not require external MCP market data. Its required data is local package content and local standards files.

| Data dependency | MCP/API/data source | Required? | Verification method | Status | Last verified |
|---|---|---|---|---|---|
| Skill package files | Local filesystem | yes | Read/write target skill directory | verified/pass | 2026-05-04 |
| Package standards | Local `references/*.md` | yes | File presence and manual review | verified/pass | 2026-05-04 |
| Validation scripts | Local `scripts/*.py` | yes | Python compile and smoke tests | verified/pass | 2026-05-04 |
| Structured audit | Local `scripts/audit_skill.py` | yes | JSON and Markdown audit report generation | verified/pass | 2026-05-04 |
| Scaffold templates | Local `templates/**/*.tmpl` | yes | Stage 1 and Stage 2 scaffold smoke tests | verified/pass | 2026-05-04 |
| Executable checks | Local `validation.checks.json` | yes | `--run-checks` execution | verified/pass | 2026-05-04 |
| Antseer frontend component standard | GitHub repo `antseer/antseer-components` plus external cache | yes for frontend-generating workflows | `scripts/sync_antseer_components.sh`; cache stays outside package source | verified/pass | 2026-05-04 |
| External MCP data | none | no | Not applicable | verified/pass | 2026-05-04 |

## Summary

All required data dependencies for this meta-skill are covered by local files. No external MCP server is required.
