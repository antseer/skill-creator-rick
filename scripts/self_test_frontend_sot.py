#!/usr/bin/env python3
"""Regression tests for the Antseer frontend Source-of-Truth gate."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_shareable_skill import validate_package  # noqa: E402


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_component_cache() -> tuple[Path, str, str]:
    """Create a local fake antseer-components git cache for deterministic tests."""
    xdg = Path(tempfile.mkdtemp(prefix="frontend-sot-cache-"))
    cache = xdg / "skill-creator-rick" / "antseer-components"
    cache.mkdir(parents=True)
    subprocess.check_call(["git", "init"], cwd=cache, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    write(cache / "README.md", "# antseer-components\n")
    subprocess.check_call(["git", "add", "README.md"], cwd=cache, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.check_call(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "fixture"],
        cwd=cache,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    full = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cache, text=True).strip()
    os.environ["XDG_CACHE_HOME"] = str(xdg)
    return cache, full[:12], full[:7]


def make_complete_skill(root: Path, commit: str | None = None, name: str = "frontend-sot-fixture") -> None:
    evidence = f"\nantseer-components inspected at commit {commit}.\n" if commit else ""
    write(
        root / "SKILL.md",
        f"""---
name: {name}
description: Validate frontend SoT gates.
---

# Frontend SoT Fixture
""",
    )
    write(
        root / "README.md",
        f"""# Frontend SoT Fixture
{evidence}
## Data Sources

| Data item | Source | Method | Last verified | Failure handling |
|---|---|---|---|---|
| Price | Verified API | API | 2026-05-04 | Error state |
| Inline frontend payload | Verified API response | fetch → validate → inject #antseer-data | 2026-05-04 | Error state |

## Validation Evidence

Verified pass with real API data. Inline data source/provenance, generated time, sample size, and time range are documented in #antseer-data.
""",
    )
    write(
        root / "README.zh.md",
        f"""# Frontend SoT Fixture
{evidence}
## 数据来源

| 数据项 | 来源 | 方法 | 最后验证 | 失败处理 |
|---|---|---|---|---|
| 价格 | 已验证 API | API | 2026-05-04 | 错误态 |
| 前端内联数据 | 已验证 API 响应 | fetch → validate → inject #antseer-data | 2026-05-04 | 错误态 |

## 验证证据

已通过真实 API 数据验证。#antseer-data 包含数据来源、生成时间、样本量和时间范围。
""",
    )
    write(root / "VERSION", "0.0.1\n")
    write(root / "agents" / "openai.yaml", f"name: {name}\n")
    write(
        root / "MCP-COVERAGE.md",
        """# MCP Coverage

All data dependencies are verified and covered by API. Inline #antseer-data provenance is verified from the same API response.
""",
    )


def make_requirement_skill(root: Path) -> None:
    write(
        root / "SKILL.md",
        """---
name: stage1-frontend
description: Stage 1 frontend fixture.
---

# Stage 1 Frontend
""",
    )
    write(
        root / "README.md",
        """# Stage 1 Frontend

## Data Reality

| Data item | Current status | Current use | Real source | Blocks Stage 2 |
|---|---|---|---|---|
| Price | Mock | Prototype | API | yes |
""",
    )
    write(
        root / "README.zh.md",
        """# Stage 1 Frontend

## 数据真实性

| 数据项 | 当前状态 | 当前用途 | 真实来源 | 是否阻塞 Stage 2 |
|---|---|---|---|---|
| 价格 | Mock | 原型 | API | 是 |
""",
    )
    write(root / "REQUIREMENT-REVIEW.md", "# Requirement Review\n")
    write(root / "TODO-TECH.md", "# TODO Tech\n")
    write(root / "TECH-INTERFACE-REQUEST.md", """# Tech Interface Request

| Item | MCP/API | Schema |
|---|---|---|
| Price | API | price:number |
""")
    write(root / "product-spec.md", "# Product Spec\n")


def write_good_frontend(path: Path) -> None:
    write(
        path,
        """<!doctype html>
<html>
<head>
<style>
:root { --antseer-primary: #36DD0C; --antseer-bg: #080807; --antseer-card: #1D1D1A; --antseer-info: #1196DD; }
.ant-card { background: var(--antseer-card); color: var(--antseer-primary); border-color: var(--antseer-info); padding: 16px; }
</style>
</head>
<body>
<main>
  <section class="ant-card">
    <div id="app">Loading Empty Error Degraded</div>
    <script id="antseer-data" type="application/json">{"source":"Verified API","generatedAt":"2026-05-04T00:00:00Z","sampleSize":1,"timeRange":"2026-05-04","items":[{"symbol":"BTC","price":1}]}</script>
    <script id="antseer-data-schema" type="application/json">{"fields":{"source":{"type":"string","required":true},"generatedAt":{"type":"datetime","required":true},"sampleSize":{"type":"number","required":true},"items.symbol":{"type":"string","required":true},"items.price":{"type":"number","required":true}}}</script>
    <script>
      function adaptPayload(payload) { return { items: payload.items, source: payload.source, state: 'loading empty error degraded' }; }
      function calculateSignal(domain) { return { ...domain, maxPrice: domain.items[0].price }; }
      function createViewModel(signal) { return { items: signal.items, source: signal.source, maxPrice: signal.maxPrice, state: signal.state }; }
      function render(viewModel) {
        document.getElementById('app').innerHTML = viewModel.items.map((item) => `<span>${item.symbol}:${item.price}</span>`).join('');
      }
      const payload = JSON.parse(document.getElementById('antseer-data').textContent);
      render(createViewModel(calculateSignal(adaptPayload(payload))));
    </script>
    <footer>Data Source: Verified API · Powered by Antseer.ai</footer>
  </section>
</main>
</body>
</html>
""",
    )


def test_bad_stage2_frontend_fails() -> None:
    _, commit12, _ = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-bad-"))
    make_complete_skill(root, commit12, name="bad-frontend-sot")
    write(
        root / "frontend" / "index.html",
        """<!doctype html>
<html>
<head>
<style>
body, .container { max-width: 960px; margin: 0 auto; padding: 24px; color: #00ffff; }
</style>
</head>
<body>
<main class="container">
  <div id="app">Price</div>
  <script id="antseer-data" type="application/json">{"price":1}</script>
  <script id="antseer-data-schema" type="application/json">{"price":"number"}</script>
  <script src="./app.js"></script>
</main>
</body>
</html>
""",
    )
    write(
        root / "frontend" / "app.js",
        """const fallbackData = {};
function render(rawPayload) {
  return rawPayload.items.map((x) => x.price).reduce((a, b) => a + b, 0);
}
document.body.insertAdjacentHTML('beforeend', 'Powered by Antseer.ai');
""",
    )

    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    required_fragments = [
        "frontend code style missing data adapter layer evidence",
        "frontend design state model must show at least 3 of loading/empty/error/degraded",
        "host-owned outer layout constraint detected",
        "non-canonical hardcoded colors",
        "fabricate fallback/default data",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in errors]
    assert not report.ok, "bad Stage 2 frontend should fail frontend SoT hard gate"
    assert not missing, "missing expected frontend SoT errors: " + ", ".join(missing)


def test_fake_component_commit_fails() -> None:
    make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-fake-commit-"))
    make_complete_skill(root, "deadbeef", name="fake-frontend-sot")
    write_good_frontend(root / "frontend" / "index.html")
    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "fake antseer-components commit should not satisfy Stage 2 frontend SoT"
    assert "package docs must record antseer-components cache commit/evidence" in errors


def test_good_stage2_frontend_passes_with_short_commit_and_viewmodel_map() -> None:
    _, _, commit7 = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-good-"))
    make_complete_skill(root, commit7, name="good-frontend-sot")
    write_good_frontend(root / "frontend" / "index.html")
    report = validate_package(root, stage="complete", run_checks=False)
    assert report.ok, "compliant Stage 2 frontend should pass: " + "\n".join(report.errors)


def test_root_html_is_gated() -> None:
    _, commit12, _ = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-root-html-"))
    make_complete_skill(root, commit12, name="root-html-sot")
    write(root / "output.html", "<html><body><main style='color:#00ffff'>No contract</main></body></html>")
    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "root output.html should be subject to frontend SoT"
    assert "output.html" in errors and "antseer-data" in errors


def test_root_html_subdir_assets_are_gated() -> None:
    _, commit12, _ = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-root-assets-"))
    make_complete_skill(root, commit12, name="root-assets-sot")
    write_good_frontend(root / "index.html")
    write(
        root / "js" / "app.js",
        """const fallbackData = {};
localStorage.setItem('bad', '1');
function render(rawPayload) {
  return rawPayload.items.map((x) => x.price).reduce((a, b) => a + b, 0);
}
""",
    )
    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "root HTML subdir JS/CSS assets must be subject to frontend SoT"
    assert "localStorage" in errors and "fallback/default data" in errors


def test_root_absolute_assets_are_gated() -> None:
    _, commit12, _ = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-root-absolute-assets-"))
    make_complete_skill(root, commit12, name="root-absolute-assets-sot")
    write_good_frontend(root / "index.html")
    path = root / "index.html"
    html = path.read_text(encoding="utf-8").replace("</body>", "<script src=\"/assets/app.js\"></script></body>")
    path.write_text(html, encoding="utf-8")
    write(
        root / "assets" / "app.js",
        """const fallbackData = {};
localStorage.setItem('bad', '1');
function render(rawPayload) {
  return rawPayload.items.map((x) => x.price).reduce((a, b) => a + b, 0);
}
""",
    )
    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "root-absolute /assets JS/CSS refs must be subject to frontend SoT"
    assert "localStorage" in errors and "fallback/default data" in errors


def test_frontend_html_root_absolute_assets_are_gated() -> None:
    _, commit12, _ = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-frontend-root-abs-assets-"))
    make_complete_skill(root, commit12, name="frontend-root-absolute-assets-sot")
    write_good_frontend(root / "frontend" / "index.html")
    path = root / "frontend" / "index.html"
    html = path.read_text(encoding="utf-8").replace("</body>", "<script src=\"/assets/app.js\"></script></body>")
    path.write_text(html, encoding="utf-8")
    write(
        root / "assets" / "app.js",
        """const fallbackData = {};
localStorage.setItem('bad', '1');
function render(rawPayload) {
  return rawPayload.items.map((x) => x.price).reduce((a, b) => a + b, 0);
}
""",
    )
    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "frontend/index.html root-absolute /assets refs must be subject to frontend SoT"
    assert "localStorage" in errors and "fallback/default data" in errors


def test_inline_json_mock_terms_fail() -> None:
    _, commit12, _ = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-inline-mock-"))
    make_complete_skill(root, commit12, name="inline-json-mock-sot")
    write_good_frontend(root / "frontend" / "index.html")
    path = root / "frontend" / "index.html"
    html = path.read_text(encoding="utf-8").replace("Verified API", "Mock API fixture", 1)
    path.write_text(html, encoding="utf-8")
    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "inline #antseer-data mock/fixture terms should fail Stage 2"
    assert "mock/fixture/synthetic/demo data terms" in errors


def test_invalid_json_contract_fails() -> None:
    _, commit12, _ = make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-json-contract-"))
    make_complete_skill(root, commit12, name="json-contract-sot")
    write(
        root / "frontend" / "index.html",
        """<!doctype html>
<html><head><style>:root { --antseer-primary:#36DD0C; --antseer-bg:#080807; }</style></head>
<body><main>
<div id="app">Loading Empty Error Degraded</div>
<script id="antseer-data" type="application/json"></script>
<script id="antseer-data-schema" type="application/json">not-json</script>
<script>function adaptPayload(payload){return payload;} function calculateSignal(domain){return domain;} function createViewModel(signal){return {items: [], signal};} function render(viewModel){document.getElementById('app').textContent = viewModel.signal.source;}</script>
<footer>Data Source: Verified API · Powered by Antseer.ai</footer>
</main></body></html>
""",
    )
    report = validate_package(root, stage="complete", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "empty/invalid inline JSON contract should fail"
    assert "#antseer-data must contain non-empty JSON" in errors


def test_stage1_missing_commit_or_deviation_docs_fails() -> None:
    make_component_cache()
    root = Path(tempfile.mkdtemp(prefix="frontend-sot-stage1-"))
    make_requirement_skill(root)
    write(root / "prototype.html", "<html><body><main style='color:#00ffff'>Prototype</main></body></html>")
    report = validate_package(root, stage="requirement", run_checks=False)
    errors = "\n".join(report.errors)
    assert not report.ok, "Stage 1 frontend must record commit evidence and disclose deviations before packaging"
    assert "package docs must record antseer-components cache commit/evidence" in errors
    assert "deviations must be recorded" in errors


if __name__ == "__main__":
    test_bad_stage2_frontend_fails()
    test_fake_component_commit_fails()
    test_good_stage2_frontend_passes_with_short_commit_and_viewmodel_map()
    test_root_html_is_gated()
    test_root_html_subdir_assets_are_gated()
    test_root_absolute_assets_are_gated()
    test_frontend_html_root_absolute_assets_are_gated()
    test_inline_json_mock_terms_fail()
    test_invalid_json_contract_fails()
    test_stage1_missing_commit_or_deviation_docs_fails()
    print("frontend SoT regression tests passed")
