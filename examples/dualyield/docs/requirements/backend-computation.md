# DualYield — Backend Computation

## L2 flow
filter → enrich probability → score → group → rank → select top candidates

## Key formulas
- Touch probability uses price / strike / volatility / tenor inputs
- Final score combines APR, safety, and venue tier bonus

## Constraints
- Computation layer must remain deterministic
- Every formula must be testable without LLM
