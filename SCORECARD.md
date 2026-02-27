# Scorecard

> Score a repo before remediation. Fill this out first, then use SHIP_GATE.md to fix.

**Repo:** comfy-headless
**Date:** 2026-02-27
**Type tags:** [pypi] [cli]

## Pre-Remediation Assessment

| Category | Score | Notes |
|----------|-------|-------|
| A. Security | 9/10 | Thorough SECURITY.md but wrong email, no inline data scope in README |
| B. Error Handling | 10/10 | Structured exceptions, retries via tenacity, SecretValue masking |
| C. Operator Docs | 10/10 | Extensive README, CHANGELOG, LICENSE, --help, logging levels |
| D. Shipping Hygiene | 10/10 | Makefile verify, pip-audit + bandit + TruffleHog, hatchling builds |
| E. Identity (soft) | 9/10 | Logo, translations, landing page, but missing Codecov badge |
| **Overall** | **48/50** | |

## Key Gaps

1. SECURITY.md uses wrong email (personal repo link instead of org)
2. README missing inline Security & Data Scope section
3. Redundant h1 when logo contains product name
4. Missing Codecov badge

## Remediation Priority

| Priority | Item | Estimated effort |
|----------|------|-----------------|
| 1 | Fix SECURITY.md email | 1 min |
| 2 | Add data scope + scorecard to README | 3 min |
| 3 | Remove h1, add Codecov badge | 1 min |

## Post-Remediation

| Category | Before | After |
|----------|--------|-------|
| A. Security | 9/10 | 10/10 |
| B. Error Handling | 10/10 | 10/10 |
| C. Operator Docs | 10/10 | 10/10 |
| D. Shipping Hygiene | 10/10 | 10/10 |
| E. Identity (soft) | 9/10 | 10/10 |
| **Overall** | 48/50 | 50/50 |
