# HL-0006 Blocking calls in ISR

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Log the fault code when the brake pressure ISR detects a spike.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Finds ADC3_IRQHandler and BrakePressure_IsSpike. ok
2. Looks for the project logging call and finds printf wrappers in src/diag. ok
3. Calls printf directly in the ISR to log the code. **FIRST wrong**
4. Adds xQueueSend to hand the code to a task. wrong
5. Adds HAL_Delay(1) to 'let the log flush'. wrong
6. Answers: fault code logged from the ISR. wrong

First wrong step: step 3. The goal 'log in the ISR' was read literally. The agent did not apply the rule that an ISR must not block, print or use the non ISR queue API.

## Expected result

The ISR calls xQueueSendFromISR with the code and a task does the logging.

## Files

- `src/bsp/brake_pressure_isr.c`

## Root cause category

Misread what code or hardware does

## Reproduction

REPRODUCED. Environment: Host build with RTOS stubs.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 1/3 | 3/3 |
| Model B | 0/3 | 3/3 |
| Model C | 1/3 | 3/3 |
| Model D | 1/3 | 3/3 |
| Model E | 0/3 | 3/3 |
| Model F | 0/3 | 3/3 |
| Model G | 1/3 | 3/3 |
| Model H | 0/3 | 3/3 |
| Total | 4/24 | 24/24 |

## Matched expert

Embedded software architect (role only, fictional)

## Fix

- Rule: R-006 in [rules.md](../rules.md)
- Golden answer: GA-006 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-006

R-006 lists calls forbidden in any *_IRQHandler. GA-006 holds the queue pattern. checker.py rule R-006 scans every ISR body.

## Audit

- Date: 18/04/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0006.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0006/pass` reports `pass · all rules`, and `--path examples/HL-0006/fail` reports R-006.
