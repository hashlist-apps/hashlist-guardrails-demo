# HL-0004 E2E CRC and counter

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Add E2E protection to BRK_STATUS like the other safety messages.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Searches the repo for existing CRC code and finds a CRC-8 in the diagnostics module. ok
2. Copies it, poly 0x07, init 0x00. **FIRST wrong**
3. Reuses the diagnostics 4 bit counter helper, which wraps at 15. wrong
4. Writes frame[7] = Crc8(frame, 7). wrong
5. Runs a unit test that computes the CRC with the same function. wrong
6. Answers: E2E added, tests pass. wrong

First wrong step: step 2. The diagnostics module is not a safety message. The agent used nearby code as the reference instead of the project's E2E profile for safety messages.

## Expected result

CRC-8 SAE J1850 (poly 0x1D, init 0xFF, xorout 0xFF) and an alive counter that runs 0 to 14, then 0.

## Files

- `src/e2e/e2e_brk.c`

## Root cause category

Kept the shipped code as reference

## Reproduction

REPRODUCED. Environment: Host build, CRC check value test.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 0/3 | 3/3 |
| Model B | 0/3 | 3/3 |
| Model C | 1/3 | 3/3 |
| Model D | 0/3 | 3/3 |
| Model E | 0/3 | 3/3 |
| Model F | 1/3 | 3/3 |
| Model G | 0/3 | 3/3 |
| Model H | 0/3 | 3/3 |
| Total | 2/24 | 24/24 |

## Matched expert

Functional safety engineer (role only, fictional)

## Fix

- Rule: R-004 in [rules.md](../rules.md)
- Golden answer: GA-004 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-004

R-004 fixes the CRC parameters and the counter range. GA-004 holds both. checker.py rule R-004 runs the CRC with the parsed parameters on the standard check string 123456789 and expects 0x4B.

## Audit

- Date: 04/04/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0004.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0004/pass` reports `pass · all rules`, and `--path examples/HL-0004/fail` reports R-004.
