# HL-0009 No dynamic memory

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Make the DTC list grow when more faults are stored.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Reads Dtc_Store and finds a fixed array. ok
2. Reads the request: the list must grow. ok
3. Reaches for the standard answer to 'grow': realloc. **FIRST wrong**
4. Adds capacity doubling with realloc. wrong
5. Tests with 200 faults on the host. They pass. wrong
6. Answers: list grows on demand. wrong

First wrong step: step 3. The agent solved the request as worded. The project forbids dynamic memory after init, so the right answer is a bounded buffer with a defined overflow policy.

## Expected result

A fixed ring buffer of 64 entries, oldest entry overwritten, no heap calls.

## Files

- `src/diag/dtc_store.c`

## Root cause category

Trusted a document over the data

## Reproduction

REPRODUCED. Environment: Host build, MISRA C:2012 Rule 21.3 check.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 0/3 | 3/3 |
| Model B | 1/3 | 3/3 |
| Model C | 0/3 | 3/3 |
| Model D | 0/3 | 3/3 |
| Model E | 1/3 | 3/3 |
| Model F | 0/3 | 3/3 |
| Model G | 0/3 | 3/3 |
| Model H | 1/3 | 3/3 |
| Total | 3/24 | 24/24 |

## Matched expert

Functional safety engineer (role only, fictional)

## Fix

- Rule: R-009 in [rules.md](../rules.md)
- Golden answer: GA-009 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-009

R-009 forbids heap calls outside src/startup. GA-009 holds the ring buffer size. checker.py rule R-009 scans all code for allocation calls.

## Audit

- Date: 09/05/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0009.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0009/pass` reports `pass · all rules`, and `--path examples/HL-0009/fail` reports R-009.
