#!/usr/bin/env python3
"""Validate an Skill package against the two-stage lifecycle.

Stage 1 / requirement: complete product plan + mock data clearly declared.
Stage 2 / complete: all user-path mocks replaced by verified real MCP/API/data sources.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# This validator rejects __pycache__ and *.pyc files as package junk. Make the
# validator itself bytecode-free even when callers forget `python -B`.
sys.dont_write_bytecode = True

from quick_validate import validate_skill

JUNK_PATTERNS = [".DS_Store", "*.pyc", "*.swp", ".*.swp"]
JUNK_DIRS = {"__pycache__"}
COMMON_REQUIRED_FILES = ["SKILL.md", "README.md", "README.zh.md"]
REQUIREMENT_REQUIRED_FILES = [
    "REQUIREMENT-REVIEW.md",
    "TODO-TECH.md",
    "TECH-INTERFACE-REQUEST.md",
]
S5_REQUIRED_FILES = [
    "VERSION",
    "data-prd.md",
    "skill-prd.md",
    "review-report.md",
    "frontend/index.html",
]
S5_REQUIRED_DIRS = [
    "layers/L1-data",
    "layers/L2-aggregation",
    "layers/L3-compute",
    "layers/L4-llm",
    "layers/L5-presentation",
]
COMPLETE_REQUIRED_FILES = [
    "VERSION",
    "agents/openai.yaml",
    "MCP-COVERAGE.md",
]
REQUIRED_INPUT_SCHEMA_FIELDS = {"type", "label", "default", "options", "description", "required"}
PRODUCT_PLAN_PATTERNS = [
    "*PRD*",
    "*prd*",
    "*spec*",
    "*SPEC*",
    "*prototype*",
    "*Prototype*",
    "*frontend*",
    "*Frontend*",
    "*backend*",
    "*Backend*",
    "design*",
    "docs*",
]
FALSE_DIRECT_USE_CLAIMS = [
    "direct-use ready",
    "ready for" + " production",
    "production" + " ready",
    "直接真实可用",
    "可直接真实可用",
    "可直接用于生产",
]
# Keep these code-shaped to avoid flagging documentation strings that merely
# explain mock/stub concepts. Stage 2 should fail when executable user-path
# logic still defines or calls mock/stub/random demo data.
USER_PATH_MOCK_PATTERNS = [
    r"\bmock_(data|rows|items|response|result|payload|source)\s*=",
    r"\b(stub|fixture)_(data|rows|items|response|result|payload|source)\s*=",
    r"\b(sample|demo|fake|dummy|placeholder)_(data|rows|items|response|result|payload|source)\s*=",
    r"\b(sample|demo|fake|dummy|placeholder)(Data|Rows|Items|Response|Result|Payload|Source)\s*=",
    r"\b(const|let|var)\s+\w*(mock|fake|dummy|placeholder)\w*\s*=",
    r"\bclass\s+(Mock|Fake|Dummy)\w*",
    r"hardcoded[_-]?(data|rows|items|response|result|payload)",
    r"hard-coded[_ -]?(data|rows|items|response|result|payload)",
    r"random\.random\s*\(",
    r"Math\.random\s*\(",
    r"faker\.",
    r"示例数据\s*=",
    r"随机生成\s*\(",
]
INLINE_JSON_MOCK_TERMS = [
    r"\bmock\b",
    r"\bstub\b",
    r"\bfixture\b",
    r"\bfake\b",
    r"\bdummy\b",
    r"\bplaceholder\b",
    r"\bsynthetic\b",
    r"\bsample\s+data\b",
    r"\bdemo\s+data\b",
    r"\brandom(?:ized|ly)?\b",
    r"模拟数据",
    r"示例数据",
    r"假数据",
    r"占位",
    r"随机",
]
CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sql", ".yaml", ".yml", ".json"}
IGNORE_MOCK_SCAN_PARTS = {"tests", "test", "fixtures", "fixture", "evals", "examples", "example", "docs", "references", "assets", "templates"}
FRONTEND_EXTENSIONS = {".html", ".css", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}
FRONTEND_SCAN_DIRS = {"frontend", "public", "src"}
FRONTEND_IGNORE_PARTS = {"tests", "test", "fixtures", "fixture", "evals", "examples", "example", "docs", "references", "assets", "templates", "node_modules", ".git"}
ROOT_FRONTEND_ASSET_DIRS = {"css", "js", "scripts", "styles"}
BANNED_FRONTEND_VENDOR_DIRS = {"antseer-components", "frontend-components", "node_modules"}
ANTSEER_CANONICAL_COLORS = {
    "#36dd0c",
    "#ffb000",
    "#1196dd",
    "#05df72",
    "#ff4444",
    "#080807",
    "#1d1d1a",
    "#121210",
    "#2a2926",
}
FRONTEND_SOT_EVIDENCE_FILES = [
    "README.md",
    "README.zh.md",
    "review-report.md",
    "TODO-TECH.md",
    "TECH-INTERFACE-REQUEST.md",
    "MCP-COVERAGE.md",
    "data-prd.md",
    "skill-prd.md",
]
FRONTEND_CODE_LAYER_PATTERNS = {
    "data adapter": r"\b(adapter|adapt[A-Z_]|adapt_|toViewModel|fromPayload|normalize[A-Z_]|normalize_)",
    "domain calculator": r"\b(calculator|calculate[A-Z_]|calculate_|compute[A-Z_]|compute_|derive[A-Z_]|derive_)",
    "view model": r"\b(viewModel|view_model|view-model|ViewModel|VIEW_MODEL)",
    "renderer": r"\b(render|renderer|Renderer|mount[A-Z_]|mount_)",
}
FRONTEND_STATE_PATTERNS = {
    "loading": r"\b(loading|isLoading|skeleton|加载)",
    "empty": r"\b(empty|isEmpty|noData|空态|无数据)",
    "error": r"\b(error|hasError|catch\s*\(|错误|失败)",
    "degraded": r"\b(degraded|stale|unavailable|fallbackState|降级|不可用)",
}
PARAM_HINT_PATTERNS = [
    r"\bparameters?\b",
    r"参数",
    r"`--[a-zA-Z0-9-]+`",
    r"\{[a-zA-Z_][a-zA-Z0-9_]*\}",
    r"<[a-zA-Z_][a-zA-Z0-9_-]*>",
]
RUN_CHECKS_FILE = "validation.checks.json"
UNRESOLVED_PLACEHOLDER_PATTERNS = [
    r"(^|\|)\s*TODO\s*(\||$)",
    r":\s*TODO(\s|$)",
    r"\bTODO_[A-Z0-9_]+\b",
    r"\bTODO MCP/API/database\b",
    r"\bReplace this\b",
    r"\{\{[^}]+\}\}",
    r"\{skill-name\}",
    r"\{remote-head-sha\}",
    r"\{synced-at\}",
    r"\{tool-name\}",
    r"\{module-name\}",
    r"\{one-line English value proposition\}",
    r"\{一句话中文核心价值\}",
]


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stage: str = "complete"

    @property
    def ok(self) -> bool:
        return not self.errors


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def has_unresolved_placeholders(text: str) -> list[str]:
    hits: list[str] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if any(token in line for token in ["`TODO`", "`Replace this`", "`{{", "`{skill-name}`", "`{remote-head-sha}`", "`{tool-name}`", "`{module-name}`"]):
            continue
        for pattern in UNRESOLVED_PLACEHOLDER_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                hits.append(f"line {i}: {line.strip()[:120]}")
                break
    return hits


def existing_files(root: Path, rels: list[str]) -> list[Path]:
    return [root / rel for rel in rels if (root / rel).exists()]


def stage2_placeholder_files(root: Path) -> list[Path]:
    """Files that must be placeholder-free before a Stage 2 package can ship."""
    files = existing_files(root, [
        "SKILL.md",
        "README.md",
        "README.zh.md",
        "MCP-COVERAGE.md",
        "VERSION",
        "skill.meta.json",
        "validation.checks.json",
        ".env.example",
    ])

    agents_dir = root / "agents"
    if agents_dir.exists():
        files.extend(p for p in agents_dir.rglob("*") if p.is_file())

    files.extend(p for p in product_plan_files(root) if "templates" not in p.relative_to(root).parts)
    return sorted(set(files))


def has_junk(root: Path) -> list[str]:
    found: list[str] = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part in JUNK_DIRS for part in rel.parts):
            found.append(str(rel))
            continue
        if any(fnmatch.fnmatch(p.name, pat) for pat in JUNK_PATTERNS):
            found.append(str(rel))
    return found


def contains_heading(text: str, headings: list[str]) -> bool:
    lowered = text.lower()
    for h in headings:
        if re.search(rf"^#+\s+.*{re.escape(h.lower())}", lowered, re.MULTILINE):
            return True
        if h.lower() in lowered:
            return True
    return False


def detect_stage(root: Path) -> str:
    """Best-effort auto detection. Explicit --stage is preferred.

    README stage markers win over instructional examples inside SKILL.md.
    This keeps meta-skills that document both stages from being misclassified.
    """
    readme = read_text(root / "README.md")
    readme_zh = read_text(root / "README.zh.md")
    readme_blob = f"{readme}\n{readme_zh}"
    readme_lower = readme_blob.lower()

    has_complete_marker = (
        "stage: complete" in readme_lower
        or "stage 2" in readme_lower and "complete" in readme_lower
        or "data sources" in readme_lower
        or "数据来源" in readme_blob
        or (root / "MCP-COVERAGE.md").exists()
    )
    has_requirement_marker = (
        "stage: requirement" in readme_lower
        or "stage 1" in readme_lower and "requirement" in readme_lower
        or "data reality" in readme_lower
        or "数据真实性" in readme_blob
        or (root / "TECH-INTERFACE-REQUEST.md").exists()
    )

    if has_complete_marker and not has_requirement_marker:
        return "complete"
    if has_requirement_marker and not has_complete_marker:
        return "requirement"
    if has_complete_marker and "validation evidence" in readme_lower:
        return "complete"
    if has_requirement_marker:
        return "requirement"

    skill_blob = read_text(root / "SKILL.md")
    skill_lower = skill_blob.lower()
    if "stage 2" in skill_lower and "complete" in skill_lower:
        return "complete"
    if "stage 1" in skill_lower and "requirement" in skill_lower:
        return "requirement"
    return "complete"


def find_product_plan_artifacts(root: Path) -> list[str]:
    found: list[str] = []
    for p in root.rglob("*"):
        if any(part in JUNK_DIRS for part in p.relative_to(root).parts):
            continue
        rel = str(p.relative_to(root))
        if rel in COMMON_REQUIRED_FILES or rel in REQUIREMENT_REQUIRED_FILES or rel in COMPLETE_REQUIRED_FILES:
            continue
        if any(fnmatch.fnmatch(p.name, pat) or fnmatch.fnmatch(rel, pat) for pat in PRODUCT_PLAN_PATTERNS):
            found.append(rel)
    return sorted(set(found))


def product_plan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in find_product_plan_artifacts(root):
        p = root / rel
        if p.is_file():
            files.append(p)
    return files


def scan_user_path_mocks(root: Path) -> list[str]:
    hits: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in CODE_EXTENSIONS:
            continue
        rel = p.relative_to(root)
        if any(part in IGNORE_MOCK_SCAN_PARTS for part in rel.parts):
            continue
        if any(part in JUNK_DIRS for part in rel.parts):
            continue
        text = read_text(p)
        for pattern in USER_PATH_MOCK_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(str(rel))
                break
    return sorted(set(hits))


def frontend_rel_ignored(rel: Path, allow_assets: bool = False) -> bool:
    ignore_parts = FRONTEND_IGNORE_PARTS - ({"assets"} if allow_assets else set())
    return any(part in ignore_parts for part in rel.parts)


def linked_frontend_assets(root: Path, html_file: Path) -> list[Path]:
    """Return local frontend assets directly referenced by a user-path HTML file."""
    root = root.resolve()
    html_file = html_file.resolve()
    text = read_text(html_file)
    refs = re.findall(r"\b(?:src|href)\s*=\s*[\"']([^\"'#?]+)", text, flags=re.IGNORECASE)
    linked: list[Path] = []
    for ref in refs:
        if re.match(r"^(?:https?:)?//|^(?:data|mailto|tel):", ref, flags=re.IGNORECASE):
            continue
        # Root-absolute refs like /assets/app.js are local to the packaged
        # static root, not filesystem /assets. They must be scanned with the
        # same hard gate as relative ./js/app.js.
        candidate = (root / ref.lstrip("/")).resolve() if ref.startswith("/") else (html_file.parent / ref).resolve()
        try:
            rel = candidate.relative_to(root)
        except ValueError:
            continue
        if not candidate.is_file() or candidate.suffix.lower() not in FRONTEND_EXTENSIONS:
            continue
        if frontend_rel_ignored(rel, allow_assets=True):
            continue
        linked.append(candidate)
    return linked


def frontend_files(root: Path) -> list[Path]:
    """Return user-path frontend files, excluding examples/templates/reference docs."""
    root = root.resolve()
    found: list[Path] = []
    root_has_html = any(
        p.is_file()
        and p.suffix.lower() == ".html"
        and len(p.relative_to(root).parts) == 1
        for p in root.glob("*.html")
    )
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in FRONTEND_EXTENSIONS:
            continue
        rel = p.relative_to(root)
        if frontend_rel_ignored(rel):
            continue
        if "frontend" in rel.parts or rel.parts[0] in FRONTEND_SCAN_DIRS:
            found.append(p)
            continue

        # Any root-level HTML is a user-path frontend entrypoint: S3/V2 pages are
        # often named output.html, prototype.html, or *-v2.html rather than
        # index.html. Once a root HTML entrypoint exists, same-directory JS/CSS is
        # part of the same user path and must not bypass the frontend gate.
        if len(rel.parts) == 1 and p.suffix.lower() == ".html":
            found.append(p)
            continue
        if len(rel.parts) == 1 and root_has_html and p.suffix.lower() in {".css", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}:
            found.append(p)
            continue
        if root_has_html and rel.parts[0] in ROOT_FRONTEND_ASSET_DIRS:
            found.append(p)

    # Follow direct local assets from every user-path HTML entrypoint, not only
    # root-level output.html/prototype.html. A normal frontend/index.html can
    # legally use root-absolute browser URLs like /assets/app.js; those are
    # package-root-relative and must be scanned by the same SoT gate.
    for html_file in [p for p in sorted(set(found)) if p.suffix.lower() == ".html"]:
        found.extend(linked_frontend_assets(root, html_file))
    return sorted(set(found))


def find_vendored_frontend_authority(root: Path) -> list[str]:
    found: list[str] = []
    for p in root.rglob("*"):
        if not p.is_dir():
            continue
        rel = p.relative_to(root)
        if any(part in {".git"} for part in rel.parts):
            continue
        if p.name in BANNED_FRONTEND_VENDOR_DIRS:
            found.append(str(rel))
    return sorted(set(found))


def selector_has_outer_layout_constraint(css_or_html: str) -> list[str]:
    """Detect common host-owned outer layout constraints on root wrappers.

    This is intentionally conservative: it only flags explicit selector blocks
    for known outer wrappers, not internal cards/grids.
    """
    hits: list[str] = []
    def is_root_selector(selector: str) -> bool:
        selector = selector.strip()
        if not selector:
            return False
        # Only root selectors themselves are host-owned. Descendant selectors
        # like `main .card` or `.container > .card` style internal components
        # and must not be blocked by the outer-layout gate.
        if re.search(r"[\s>+~]", selector):
            return False
        root_patterns = [
            r"body(?:[.#:\[].*)?",
            r"main(?:[.#:\[].*)?",
            r"#(?:app|root)(?:[:\[].*)?",
            r"\.(?:container|app|skill-root|antseer-root|page)(?:[.#:\[].*)?",
        ]
        return any(re.fullmatch(pattern, selector, flags=re.IGNORECASE) for pattern in root_patterns)

    block_re = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]+)\}", re.IGNORECASE | re.MULTILINE)
    for m in block_re.finditer(css_or_html):
        body = m.group("body")
        selectors = [s.strip() for s in m.group("selector").split(",")]
        root_selectors = [s for s in selectors if is_root_selector(s)]
        if not root_selectors:
            continue
        selector = ", ".join(root_selectors)
        bad_props = []
        if re.search(r"\bmax-width\s*:", body, flags=re.IGNORECASE):
            bad_props.append("max-width")
        if re.search(r"\bmargin\s*:\s*0\s+auto\b", body, flags=re.IGNORECASE):
            bad_props.append("margin: 0 auto")
        if re.search(r"\bpadding(?:-\w+)?\s*:", body, flags=re.IGNORECASE):
            bad_props.append("root padding")
        if bad_props:
            hits.append(f"{selector}: {', '.join(sorted(set(bad_props)))}")
    return hits


def antseer_components_cache_commit() -> str | None:
    cache_home = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    cache = cache_home / "skill-creator-rick" / "antseer-components"
    if not (cache / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(cache), "rev-parse", "--short=12", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{7,40}", commit) else None


def frontend_sot_evidence_text(root: Path) -> str:
    chunks: list[str] = []
    for rel in FRONTEND_SOT_EVIDENCE_FILES:
        p = root / rel
        if p.exists() and p.is_file():
            chunks.append(read_text(p))
    return "\n".join(chunks)


def has_component_commit_evidence(root: Path, current_commit: str | None = None) -> bool:
    evidence = frontend_sot_evidence_text(root)
    if "antseer-components" not in evidence and "Frontend SoT" not in evidence and "组件库" not in evidence:
        return False
    if not current_commit:
        return False
    # sync_antseer_components.sh historically printed git's default 7-char %h,
    # while the validator used --short=12. Accept only prefixes of the current
    # local cache HEAD so copied 7/12/40-char evidence works without accepting an
    # unrelated fake hash.
    hexes = re.findall(r"\b[0-9a-f]{7,40}\b", evidence, flags=re.IGNORECASE)
    current = current_commit.lower()
    return any(current.startswith(h.lower()) or h.lower().startswith(current) for h in hexes)


def frontend_stage1_deviation_documented(root: Path) -> bool:
    evidence = frontend_sot_evidence_text(root)
    if not evidence.strip():
        return False
    return bool(re.search(
        r"(antseer-components|Frontend SoT|前端).{0,160}(deviation|gap|blocker|偏差|缺口|整改|Stage 2|阶段 2)",
        evidence,
        flags=re.IGNORECASE | re.DOTALL,
    ))


def stage1_deviation_disclosure_gaps(root: Path, soft_misses: list[str]) -> list[str]:
    """Require Stage 1 frontend deviation docs to name each miss category.

    A generic "frontend has Stage 2 blockers" sentence is not enough; handoff
    packages must tell Stage 2 implementers which code/UI/design contract is
    still off-standard.
    """
    if not soft_misses:
        return []
    evidence = frontend_sot_evidence_text(root)
    if not frontend_stage1_deviation_documented(root):
        return ["missing frontend deviation disclosure"]

    category_patterns = [
        ("storage", r"localStorage|sessionStorage|storage|存储"),
        ("mock data", r"mock|stub|fixture|fake|dummy|placeholder|synthetic|demo data|sample data|模拟|示例|假数据|占位"),
        ("design tokens/palette", r"token|palette|color|颜色|色板|设计规范|canonical"),
        ("source footer", r"footer|source footer|Powered by Antseer|Data Source|数据来源|来源页脚"),
        ("outer layout", r"layout|max-width|padding|margin|container|外层|宿主|布局"),
        ("code layering", r"adapter|calculator|view model|renderer|分层|渲染|计算|业务逻辑"),
        ("JSON data contract", r"#antseer-data|antseer-data-schema|JSON|schema|contract|数据契约|官网 JSON"),
        ("fallback/default data", r"fallback|default|降级|默认数据"),
    ]
    needed: set[tuple[str, str]] = set()
    for miss in soft_misses:
        lower = miss.lower()
        if "localstorage" in lower or "sessionstorage" in lower:
            needed.add(category_patterns[0])
        if any(token in lower for token in ["mock", "stub", "random", "demo", "fixture", "synthetic"]):
            needed.add(category_patterns[1])
        if any(token in lower for token in ["token", "palette", "color"]):
            needed.add(category_patterns[2])
        if "footer" in lower or "source" in lower:
            needed.add(category_patterns[3])
        if "layout" in lower or "outer" in lower or "max-width" in lower:
            needed.add(category_patterns[4])
        if any(token in lower for token in ["adapter", "calculator", "view model", "renderer", "compute", "layer"]):
            needed.add(category_patterns[5])
        if "antseer-data" in lower or "json" in lower or "schema" in lower or "contract" in lower:
            needed.add(category_patterns[6])
        if "fallback" in lower or "default data" in lower:
            needed.add(category_patterns[7])

    gaps = []
    for label, pattern in sorted(needed):
        if not re.search(pattern, evidence, flags=re.IGNORECASE):
            gaps.append(label)
    return gaps


def frontend_code_style_misses(aggregate: str) -> list[str]:
    misses: list[str] = []
    for label, pattern in FRONTEND_CODE_LAYER_PATTERNS.items():
        if not re.search(pattern, aggregate, flags=re.IGNORECASE):
            misses.append(f"frontend code style missing {label} layer evidence")

    state_hits = [
        label
        for label, pattern in FRONTEND_STATE_PATTERNS.items()
        if re.search(pattern, aggregate, flags=re.IGNORECASE)
    ]
    if len(state_hits) < 3:
        misses.append("frontend design state model must show at least 3 of loading/empty/error/degraded")

    renderer_fetch_patterns = [
        r"\b(render|renderer|mount)\w*\s*(?:=|:)?\s*(?:function)?[^{=]*\{[^}]{0,1200}\bfetch\s*\(",
        r"\b(render|renderer|mount)\w*\s*=>\s*\{[^}]{0,1200}\bfetch\s*\(",
    ]
    if any(re.search(pattern, aggregate, flags=re.IGNORECASE | re.DOTALL) for pattern in renderer_fetch_patterns):
        misses.append("renderer appears to fetch raw data; move data access into adapter")

    renderer_calc_patterns = [
        r"\b(render|renderer|mount)\w*\s*(?:=|:)?\s*(?:function)?[^{=]*\{[^}]{0,1200}(?<!\.)\b(?!viewModel\b)[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*){0,3}\.(reduce|filter|sort)\s*\(",
        r"\b(render|renderer|mount)\w*\s*(?:=|:)?\s*(?:function)?[^{=]*\{[^}]{0,1200}(?<!\.)\b(?:raw|payload|data|domain|rows|items)[A-Za-z_$\w]*(?:\.[A-Za-z_$][\w$]*){0,3}\.map\s*\(",
    ]
    if any(re.search(pattern, aggregate, flags=re.IGNORECASE | re.DOTALL) for pattern in renderer_calc_patterns):
        misses.append("renderer appears to compute business/domain transformations; move logic into calculator/view model")

    fallback_patterns = [
        r"\b(fallback|default)(Data|Rows|Items|Payload|Source)\s*=",
        r"\|\|\s*(\[\]|\{\})\s*;?\s*(//.*)?$",
    ]
    if any(re.search(pattern, aggregate, flags=re.IGNORECASE | re.MULTILINE) for pattern in fallback_patterns):
        misses.append("frontend appears to fabricate fallback/default data")

    return misses


def strip_json_script_blocks(text: str) -> str:
    return re.sub(
        r"<script\b(?=[^>]*\btype=[\"']application/json[\"'])[^>]*>.*?</script>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )


def extract_inline_json_script(html: str, element_id: str) -> tuple[object | None, str | None]:
    pattern = re.compile(
        rf"<script\b(?=[^>]*\bid=[\"']{re.escape(element_id)}[\"'])(?P<attrs>[^>]*)>(?P<body>.*?)</script>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return None, f"missing #{element_id}"
    attrs = match.group("attrs")
    if not re.search(r"\btype=[\"']application/json[\"']", attrs, flags=re.IGNORECASE):
        return None, f"#{element_id} must be type=\"application/json\""
    body = match.group("body").strip()
    if not body:
        return None, f"#{element_id} must contain non-empty JSON"
    try:
        parsed = json.loads(body)
    except Exception as e:
        return None, f"#{element_id} is not valid JSON: {e}"
    if not parsed:
        return None, f"#{element_id} must contain a non-empty JSON object/array"
    if not isinstance(parsed, (dict, list)):
        return None, f"#{element_id} must contain a JSON object or array"
    return parsed, None


def json_keys(obj: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.add(str(key))
            keys.update(json_keys(value))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(json_keys(item))
    return keys


def inline_data_has_provenance(data: object, evidence_text: str) -> bool:
    keys = {k.lower().replace("_", "").replace("-", "") for k in json_keys(data)}
    provenance_keys = {
        "source",
        "sources",
        "datasource",
        "datasources",
        "provenance",
        "generatedat",
        "verifiedat",
        "lastverified",
        "timerange",
        "samplesize",
        "mcp",
        "api",
    }
    if keys & provenance_keys:
        return True
    return bool(re.search(
        r"(#antseer-data|inline data|内联数据|官网 JSON).{0,240}(source|data source|provenance|verified|generated|sample|time range|数据来源|来源|验证|生成|样本|时间范围)",
        evidence_text,
        flags=re.IGNORECASE | re.DOTALL,
    ))


def frontend_json_contract_misses(root: Path, html: Path, text: str) -> list[str]:
    rel = html.relative_to(root)
    misses: list[str] = []
    data, data_error = extract_inline_json_script(text, "antseer-data")
    schema, schema_error = extract_inline_json_script(text, "antseer-data-schema")
    if data_error:
        misses.append(f"{rel} {data_error} payload for official JSON-template delivery")
    if schema_error:
        misses.append(f"{rel} {schema_error} contract")
    if data_error or schema_error:
        return misses

    assert data is not None and schema is not None
    if isinstance(schema, list):
        misses.append(f"{rel} #antseer-data-schema must be a JSON object describing fields/contracts")
    elif not json_keys(schema):
        misses.append(f"{rel} #antseer-data-schema must describe at least one field/contract key")

    serialized_data = json.dumps(data, ensure_ascii=False)
    if any(re.search(pattern, serialized_data, flags=re.IGNORECASE) for pattern in USER_PATH_MOCK_PATTERNS):
        misses.append(f"{rel} #antseer-data appears to contain mock/stub/random/demo data patterns")
    if any(re.search(pattern, serialized_data, flags=re.IGNORECASE) for pattern in INLINE_JSON_MOCK_TERMS):
        misses.append(f"{rel} #antseer-data appears to contain mock/fixture/synthetic/demo data terms")

    if not inline_data_has_provenance(data, frontend_sot_evidence_text(root)):
        misses.append(f"{rel} #antseer-data must include or document source/provenance/verification evidence")

    return misses


def frontend_ui_style_misses(aggregate: str) -> list[str]:
    misses: list[str] = []
    style_text = strip_json_script_blocks(aggregate)
    hexes = set(re.findall(r"#[0-9a-fA-F]{6}\b", style_text))
    noncanonical = sorted(h for h in hexes if h.lower() not in ANTSEER_CANONICAL_COLORS)
    if noncanonical:
        misses.append("frontend contains non-canonical hardcoded colors: " + ", ".join(noncanonical[:10]))
    return misses


def validate_frontend_sot(root: Path, stage: str) -> tuple[list[str], list[str]]:
    """Apply antseer-components as frontend SoT.

    Stage 1 treats most compliance misses as warnings because the package may
    be a handoff prototype. Stage 2 turns the same misses into hard errors.
    Vendoring the authority repo/cache is always an error.
    """
    # Normalize once so paths returned by frontend_files()/linked assets and
    # paths used for reporting share the same /var vs /private/var spelling on
    # macOS temp dirs. Otherwise Path.relative_to() can fail even for children.
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    files = frontend_files(root)
    has_frontend = bool(files) or (root / "frontend").exists()
    if not has_frontend:
        return errors, warnings

    vendored = find_vendored_frontend_authority(root)
    if vendored:
        errors.append("Do not vendor frontend authority/cache into the skill package: " + ", ".join(vendored))

    html_files = [p for p in files if p.suffix.lower() == ".html"]
    aggregate = "\n".join(read_text(p) for p in files)
    soft_misses: list[str] = []
    stage1_hard_misses: list[str] = []
    current_commit = antseer_components_cache_commit()
    has_commit_evidence = has_component_commit_evidence(root, current_commit)

    if not current_commit:
        stage1_hard_misses.append("antseer-components local cache is missing or not a readable git checkout")
    if not has_commit_evidence:
        stage1_hard_misses.append("package docs must record antseer-components cache commit/evidence")

    if "localStorage" in aggregate or "sessionStorage" in aggregate:
        soft_misses.append("frontend must not use localStorage/sessionStorage")

    if any(re.search(pattern, aggregate, flags=re.IGNORECASE) for pattern in USER_PATH_MOCK_PATTERNS):
        soft_misses.append("frontend user path contains mock/stub/random/demo data patterns")

    if not re.search(r"--antseer-|var\(--antseer-|#(?:36dd0c|ffb000|1196dd|05df72|ff4444|080807|1d1d1a|121210|2a2926)\b", aggregate, flags=re.IGNORECASE):
        soft_misses.append("frontend does not visibly use Antseer design tokens/canonical palette")

    if not re.search(r"Powered by Antseer|Antseer\.ai|数据来源|Data Source|source footer", aggregate, flags=re.IGNORECASE):
        soft_misses.append("frontend must expose Antseer/source footer")

    layout_hits: list[str] = []
    for p in files:
        text = read_text(p)
        for hit in selector_has_outer_layout_constraint(text):
            layout_hits.append(f"{p.relative_to(root)} {hit}")
    if layout_hits:
        soft_misses.append("host-owned outer layout constraint detected: " + "; ".join(layout_hits[:5]))

    if stage == "complete":
        soft_misses.extend(frontend_code_style_misses(aggregate))
        soft_misses.extend(frontend_ui_style_misses(aggregate))

    for html in html_files:
        text = read_text(html)
        rel = html.relative_to(root)
        soft_misses.extend(frontend_json_contract_misses(root, html, text))

    if stage == "complete":
        soft_misses.extend(stage1_hard_misses)
        errors.extend(f"Stage 2 frontend SoT gate: {miss}" for miss in sorted(set(soft_misses)))
    else:
        errors.extend(f"Stage 1 frontend SoT gate: {miss}" for miss in sorted(set(stage1_hard_misses)))
        warnings.extend(f"Stage 1 frontend SoT best-effort: {miss}" for miss in sorted(set(soft_misses)))
        disclosure_gaps = stage1_deviation_disclosure_gaps(root, sorted(set(soft_misses)))
        if disclosure_gaps:
            errors.append(
                "Stage 1 frontend SoT gate: concrete deviations must be recorded in "
                "review-report/TODO-TECH/TECH-INTERFACE-REQUEST: " + ", ".join(disclosure_gaps)
            )

    return errors, warnings


def option_values(options: object) -> list[object]:
    if not isinstance(options, list):
        return []
    values = []
    for opt in options:
        if isinstance(opt, dict) and "value" in opt:
            values.append(opt["value"])
    return values


def validate_input_schema(root: Path) -> list[str]:
    path = root / "skill.meta.json"
    if not path.exists():
        return []

    try:
        obj = json.loads(read_text(path))
    except Exception as e:
        return [f"skill.meta.json is not valid JSON: {e}"]

    if "input_schema" not in obj:
        return []

    schema = obj["input_schema"]
    errors: list[str] = []
    if not isinstance(schema, dict):
        return ["input_schema must be an object"]

    zh = schema.get("zh")
    en = schema.get("en")
    if not isinstance(zh, dict) or not isinstance(en, dict):
        return ["input_schema must contain both zh and en objects"]

    if set(zh.keys()) != set(en.keys()):
        errors.append("input_schema zh/en parameter keys must match exactly")

    for lang, block in [("zh", zh), ("en", en)]:
        for key, cfg in block.items():
            if not isinstance(cfg, dict):
                errors.append(f"input_schema.{lang}.{key} must be an object")
                continue
            missing = REQUIRED_INPUT_SCHEMA_FIELDS - set(cfg.keys())
            if missing:
                errors.append(f"input_schema.{lang}.{key} missing fields: {', '.join(sorted(missing))}")
                continue
            if cfg.get("type") not in {"input", "select", "multiple"}:
                errors.append(f"input_schema.{lang}.{key}.type must be input/select/multiple")
            if not isinstance(cfg.get("options"), list):
                errors.append(f"input_schema.{lang}.{key}.options must be an array")
            else:
                for i, opt in enumerate(cfg["options"]):
                    if not isinstance(opt, dict) or "label" not in opt or "value" not in opt:
                        errors.append(f"input_schema.{lang}.{key}.options[{i}] must contain label and value")
            if not isinstance(cfg.get("required"), bool):
                errors.append(f"input_schema.{lang}.{key}.required must be boolean")
            if cfg.get("type") == "input" and cfg.get("options") != []:
                errors.append(f"input_schema.{lang}.{key}.options must be [] for input type")
            if cfg.get("type") == "select":
                values = option_values(cfg.get("options"))
                if values and cfg.get("default") not in values:
                    errors.append(f"input_schema.{lang}.{key}.default must exist in options[].value for select type")
            if cfg.get("type") == "multiple":
                default = cfg.get("default")
                if not isinstance(default, list):
                    errors.append(f"input_schema.{lang}.{key}.default must be an array for multiple type")
                else:
                    values = option_values(cfg.get("options"))
                    missing_defaults = [v for v in default if v not in values]
                    if values and missing_defaults:
                        errors.append(f"input_schema.{lang}.{key}.default values not found in options[].value: {missing_defaults}")

    for key in set(zh.keys()) & set(en.keys()):
        z = zh.get(key, {})
        e = en.get(key, {})
        if not isinstance(z, dict) or not isinstance(e, dict):
            continue
        for field in ["type", "default", "required"]:
            if z.get(field) != e.get(field):
                errors.append(f"input_schema.{key}.{field} must match between zh and en")
        if option_values(z.get("options")) != option_values(e.get("options")):
            errors.append(f"input_schema.{key}.options[].value must match between zh and en")

    return errors


def maybe_warn_missing_input_schema(root: Path) -> list[str]:
    meta_path = root / "skill.meta.json"
    has_schema = False
    if meta_path.exists():
        try:
            meta = json.loads(read_text(meta_path))
            schema = meta.get("input_schema")
            has_schema = isinstance(schema, dict) and bool(schema.get("zh") or schema.get("en"))
        except Exception:
            has_schema = False
    if has_schema:
        return []

    blob = "\n".join(read_text(root / name) for name in ["SKILL.md", "README.md", "README.zh.md"])
    if any(re.search(pattern, blob, flags=re.IGNORECASE) for pattern in PARAM_HINT_PATTERNS):
        return ["Possible user parameters detected, but skill.meta.json > input_schema is empty or missing"]
    return []


def load_run_checks(root: Path) -> tuple[list[dict], list[str]]:
    path = root / RUN_CHECKS_FILE
    if not path.exists():
        return [], [f"--run-checks requested but {RUN_CHECKS_FILE} is missing"]
    try:
        obj = json.loads(read_text(path))
    except Exception as e:
        return [], [f"{RUN_CHECKS_FILE} is not valid JSON: {e}"]
    checks = obj.get("checks") if isinstance(obj, dict) else None
    if not isinstance(checks, list) or not checks:
        return [], [f"{RUN_CHECKS_FILE} must contain a non-empty checks array"]
    errors = []
    normalized = []
    for i, check in enumerate(checks):
        if not isinstance(check, dict):
            errors.append(f"{RUN_CHECKS_FILE}.checks[{i}] must be an object")
            continue
        name = check.get("name", f"check-{i + 1}")
        command = check.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
            errors.append(f"{RUN_CHECKS_FILE}.checks[{i}].command must be a non-empty string array")
            continue
        try:
            timeout_seconds = int(check.get("timeout_seconds", 60))
        except (TypeError, ValueError):
            errors.append(f"{RUN_CHECKS_FILE}.checks[{i}].timeout_seconds must be a positive integer")
            continue
        if timeout_seconds <= 0:
            errors.append(f"{RUN_CHECKS_FILE}.checks[{i}].timeout_seconds must be a positive integer")
            continue
        normalized.append({
            "name": str(name),
            "command": command,
            "timeout_seconds": timeout_seconds,
        })
    return normalized, errors


def run_executable_checks(root: Path) -> list[str]:
    checks, errors = load_run_checks(root)
    if errors:
        return errors
    run_errors = []
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for check in checks:
        try:
            result = subprocess.run(
                check["command"],
                cwd=root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=check["timeout_seconds"],
                check=False,
            )
        except subprocess.TimeoutExpired:
            run_errors.append(f"Run check timed out: {check['name']}")
            continue
        except Exception as e:
            run_errors.append(f"Run check failed to start: {check['name']}: {e}")
            continue
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip().splitlines()
            snippet = details[-1] if details else "no output"
            run_errors.append(f"Run check failed: {check['name']} exited {result.returncode}: {snippet}")
    return run_errors


def validate_requirement(root: Path) -> list[str]:
    errors: list[str] = []
    readme = read_text(root / "README.md")
    readme_zh = read_text(root / "README.zh.md")
    blob = "\n".join([readme, readme_zh, read_text(root / "SKILL.md")])

    for rel in REQUIREMENT_REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"Stage 1 semi-finished package missing: {rel}")

    if not contains_heading(readme, ["Data Reality"]):
        errors.append("README.md must contain a Data Reality section for Stage 1")
    if not contains_heading(readme_zh, ["数据真实性"]):
        errors.append("README.zh.md must contain a 数据真实性 section for Stage 1")

    if not find_product_plan_artifacts(root):
        errors.append("Stage 1 requires at least one product plan artifact (PRD/spec/prototype/frontend/backend/docs)")

    placeholder_files = [
        root / "README.md",
        root / "README.zh.md",
        root / "SKILL.md",
        root / "REQUIREMENT-REVIEW.md",
        root / "TECH-INTERFACE-REQUEST.md",
    ] + product_plan_files(root)
    for p in placeholder_files:
        if not p.exists() or not p.is_file():
            continue
        hits = has_unresolved_placeholders(read_text(p))
        if hits:
            errors.append(f"Unresolved placeholders in {p.relative_to(root)}: " + "; ".join(hits[:3]))

    lower = blob.lower()
    for claim in FALSE_DIRECT_USE_CLAIMS:
        if claim in lower or claim in blob:
            errors.append(f"Stage 1 must not claim direct-use readiness: found '{claim}'")

    tech_request = read_text(root / "TECH-INTERFACE-REQUEST.md")
    if (root / "TECH-INTERFACE-REQUEST.md").exists():
        needed_terms = ["mcp", "api", "接口", "数据", "schema"]
        if not any(term in tech_request.lower() for term in needed_terms):
            errors.append("TECH-INTERFACE-REQUEST.md should list MCP/API/data/schema requirements")
        if not re.search(r"\|.+\|.+\|.+\|", tech_request):
            errors.append("TECH-INTERFACE-REQUEST.md should include concrete tables for data/interface requirements")

    readme_hits = re.findall(r"\|\s*TODO\s*\|", readme, flags=re.IGNORECASE)
    if readme_hits:
        errors.append("README.md Data Reality appears to contain only template TODO rows")

    errors.extend(validate_s5_semifinished(root))

    return errors


def validate_s5_semifinished(root: Path) -> list[str]:
    """Validate the stricter Antseer S5 semi-finished structure when present.

    Stage 1 Lite packages do not need this. If any S5-specific artifact exists,
    the whole S5 handoff skeleton must be coherent.
    """
    markers = ["data-prd.md", "skill-prd.md", "frontend", "layers", "mcp-audit.md"]
    if not any((root / m).exists() for m in markers):
        return []

    errors: list[str] = []
    for rel in S5_REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"S5 semi-finished package missing: {rel}")
    for rel in S5_REQUIRED_DIRS:
        if not (root / rel).is_dir():
            errors.append(f"S5 semi-finished package missing directory: {rel}")
        elif not (root / rel / "README.md").exists():
            errors.append(f"S5 layer missing README.md: {rel}")

    for rel in ["data-prd.md", "skill-prd.md", "review-report.md", "mcp-audit.md"]:
        p = root / rel
        if p.exists():
            hits = has_unresolved_placeholders(read_text(p))
            if hits:
                errors.append(f"Unresolved placeholders in {rel}: " + "; ".join(hits[:3]))

    skill_prd = read_text(root / "skill-prd.md")
    data_prd = read_text(root / "data-prd.md")
    if (root / "skill-prd.md").exists():
        for token in ["L1", "L2", "L3", "L4", "L5", "附录 A"]:
            if token not in skill_prd:
                errors.append(f"skill-prd.md must explicitly cover {token}")
    if (root / "data-prd.md").exists():
        for token in ["P0", "期望接口", "降级", "验收"]:
            if token not in data_prd:
                errors.append(f"data-prd.md must include {token}")
    return errors


def validate_complete(root: Path, run_checks: bool = False) -> list[str]:
    errors: list[str] = []
    readme = read_text(root / "README.md")
    readme_zh = read_text(root / "README.zh.md")

    for rel in COMPLETE_REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"Stage 2 complete package missing: {rel}")

    if not contains_heading(readme, ["Data Sources"]):
        errors.append("README.md must contain a Data Sources section for Stage 2")
    if not contains_heading(readme, ["Validation Evidence"]):
        errors.append("README.md must contain a Validation Evidence section for Stage 2")
    if not contains_heading(readme_zh, ["数据来源"]):
        errors.append("README.zh.md must contain a 数据来源 section for Stage 2")
    if not contains_heading(readme_zh, ["验证证据"]):
        errors.append("README.zh.md must contain a 验证证据 section for Stage 2")

    coverage = read_text(root / "MCP-COVERAGE.md")
    if (root / "MCP-COVERAGE.md").exists():
        lower = coverage.lower()
        if "mcp" not in lower and "api" not in lower and "数据源" not in coverage:
            errors.append("MCP-COVERAGE.md must describe MCP/API/data-source coverage")
        if not any(term in lower for term in ["verified", "pass", "covered", "验证", "已覆盖", "通过"]):
            errors.append("MCP-COVERAGE.md must include verification status/evidence")

    mock_hits = scan_user_path_mocks(root)
    if mock_hits:
        errors.append("Stage 2 user-path code appears to still contain mock/stub/random data: " + ", ".join(mock_hits))

    validation_blob = readme + "\n" + readme_zh + "\n" + coverage
    if "TODO" in validation_blob or "待补" in validation_blob:
        errors.append("Stage 2 docs must not contain unresolved TODO/待补 placeholders in README or MCP-COVERAGE.md")

    for p in stage2_placeholder_files(root):
        if not p.exists() or not p.is_file():
            continue
        hits = has_unresolved_placeholders(read_text(p))
        if hits:
            errors.append(f"Unresolved placeholders in {p.relative_to(root)}: " + "; ".join(hits[:3]))

    if run_checks:
        errors.extend(run_executable_checks(root))

    return errors


def validate_package(root: Path, stage: str = "auto", run_checks: bool = False) -> ValidationReport:
    actual_stage = detect_stage(root) if stage == "auto" else stage
    report = ValidationReport(stage=actual_stage)

    valid, message = validate_skill(root)
    if not valid:
        report.errors.append(message)

    for rel in COMMON_REQUIRED_FILES:
        if not (root / rel).exists():
            report.errors.append(f"Missing required file: {rel}")

    junk = has_junk(root)
    if junk:
        report.errors.append("Junk files present: " + ", ".join(sorted(junk)))

    report.errors.extend(validate_input_schema(root))
    report.warnings.extend(maybe_warn_missing_input_schema(root))

    if actual_stage == "requirement":
        report.errors.extend(validate_requirement(root))
    elif actual_stage == "complete":
        report.errors.extend(validate_complete(root, run_checks=run_checks))

    frontend_errors, frontend_warnings = validate_frontend_sot(root, actual_stage)
    report.errors.extend(frontend_errors)
    report.warnings.extend(frontend_warnings)

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_path")
    parser.add_argument("--stage", choices=["auto", "requirement", "complete"], default="auto")
    parser.add_argument("--run-checks", action="store_true", help=f"For Stage 2, execute commands from {RUN_CHECKS_FILE}")
    args = parser.parse_args()

    root = Path(args.skill_path).resolve()
    report = validate_package(root, stage=args.stage, run_checks=args.run_checks)

    if report.errors:
        print(f"Skill package validation failed for stage: {report.stage}\n")
        for e in report.errors:
            print(f"- {e}")
        if report.warnings:
            print("\nWarnings:\n")
            for w in report.warnings:
                print(f"- {w}")
        return 1

    print(f"Skill package is valid for stage: {report.stage}")
    if report.warnings:
        print("\nWarnings:\n")
        for w in report.warnings:
            print(f"- {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
