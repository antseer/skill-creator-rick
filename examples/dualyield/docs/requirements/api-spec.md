# DualYield — API Spec

## Primary sources
- Antseer dual-investment aggregate endpoint
- Binance / other CEX DCI product endpoints
- Market price and volatility sources for underlying assets

## Internal schema
Required normalized fields: platform, side, strike, duration, apr, probability, distance, min amount, settlement info, and risk labels.

## Degrade strategy
- Prefer Antseer aggregate
- Fallback to direct venue fetches
- If only partial venues succeed, return partial results with venue-level warning
