# DualYield — Implementation Guide

## Binding
- L1 fetches products and market context
- L2 computes ranked candidates
- L3 produces headline, reasons, and risk framing
- L4 renders hero, evidence, and trust layers

## Production vs prototype
- `implementation/frontend/dualyield.html` is prototype-only
- Real data injection must come from `implementation/pipeline/orchestrator.py`

## Priority gaps
See `../handoff/docs/handoff/TODO-TECH.md`.
