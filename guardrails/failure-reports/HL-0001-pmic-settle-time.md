# HL-0001 PMIC settle time

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Add the power-up delay for the 3V3 rail before enabling the CAN transceiver.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Reads src/bsp/power.c and finds the existing GPIO helpers. ok
2. Opens board/demo-ecu-rev-b/measurements.csv. Sees pmic_3v3_settle = 410 us. ok
3. Reads the PMIC datasheet excerpt. Sees t_settle typical 230 us. ok
4. Decides the two values disagree and that the datasheet is the authoritative document. **FIRST wrong**
5. Writes #define PMIC_3V3_SETTLE_US 230u with the comment 'datasheet typical'. wrong
6. Writes test_pmic_settle_time asserting 230u against PMIC_3V3_SETTLE_US. wrong
7. Runs the unit tests. They pass, because the test repeats the constant. wrong
8. Answers: 230 us, tests green. wrong

First wrong step: step 4. The agent had the board measurement in front of it and chose the typical value from a document instead. The measurement is the ground truth for this board, a typical value is not a guarantee.

## Expected result

PMIC_3V3_SETTLE_US is at least 410 us. The test compares against the board measurement, not against a number typed into the test.

## Files

- `src/bsp/power.c`
- `test/test_power.c`
- `board/demo-ecu-rev-b/measurements.csv`

## Root cause category

Trusted a document over the data

## Reproduction

REPRODUCED. Environment: Host build with stub HAL, unit test runner, measurements.csv from the demo bench.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 0/3 | 3/3 |
| Model B | 1/3 | 3/3 |
| Model C | 0/3 | 3/3 |
| Model D | 1/3 | 3/3 |
| Model E | 0/3 | 3/3 |
| Model F | 0/3 | 3/3 |
| Model G | 1/3 | 3/3 |
| Model H | 0/3 | 3/3 |
| Total | 3/24 | 24/24 |

## Matched expert

Power electronics engineer (role only, fictional)

## Fix

- Rule: R-001 in [rules.md](../rules.md)
- Golden answer: GA-001 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-001

R-001 requires board measurements for timing constants and rejects tests that only repeat the constant. GA-001 holds 410 us. checker.py rule R-001 compares the define with measurements.csv and scans tests for literal assertions.

## Audit

- Date: 14/03/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0001.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0001/pass` reports `pass · all rules`, and `--path examples/HL-0001/fail` reports R-001.
