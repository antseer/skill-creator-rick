# DualYield — Business Spec

## Product goal
Help users find dual-investment candidates that maximize yield while keeping touch probability aligned with risk preference.

## Core rules
- Hero must surface Top 1 recommendation first.
- Top list defaults to 3 candidates.
- Recommendation must balance APR, touch probability, duration, and venue trust.
- Every recommendation must include risk note and exercise context.

## Edge handling
- If live product data is unavailable, show explicit data warning.
- If screening leaves fewer than 3 candidates, show remaining valid candidates only.
- If volatility or price context is missing, degrade recommendation confidence.

## Success
- User understands top recommendation in under 10 seconds.
- Engineer can implement without re-deriving product rules from the PRD.
