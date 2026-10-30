# HL-0005 Shared ISR variable

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Count CAN RX overruns in the ISR and report them every 100 ms.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Finds FDCAN1_IT0_IRQHandler and the overrun flag helpers. ok
2. Declares static uint64_t g_can_rx_overruns to be safe against wrap. ok
3. Increments it in the ISR. ok
4. Reads it in the 100 ms task with a plain assignment, assuming the load is atomic. **FIRST wrong**
5. Omits volatile, since the compiler 'sees' the ISR. wrong
6. Answers: counter implemented. wrong

First wrong step: step 4. On a 32-bit Cortex-M7 a 64-bit load is two instructions. An interrupt between them gives a torn value. The agent applied 64-bit width as a safety measure and missed this side effect.

## Expected result

The variable is volatile and the task reads it between __disable_irq() and __enable_irq(), or through the snapshot helper.

## Files

- `src/can/can_diag.c`

## Root cause category

Misread what code or hardware does

## Reproduction

REPRODUCED. Environment: Host build, static analysis of ISR written variables.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 0/3 | 3/3 |
| Model B | 1/3 | 3/3 |
| Model C | 0/3 | 3/3 |
| Model D | 0/3 | 3/3 |
| Model E | 1/3 | 3/3 |
| Model F | 1/3 | 3/3 |
| Model G | 0/3 | 3/3 |
| Model H | 0/3 | 3/3 |
| Total | 3/24 | 24/24 |

## Matched expert

Embedded software architect (role only, fictional)

## Fix

- Rule: R-005 in [rules.md](../rules.md)
- Golden answer: GA-005 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-005

R-005 requires volatile on ISR written variables and a critical section for 64-bit reads. GA-005 holds the pattern. checker.py rule R-005 finds ISR writes and checks every reader.

## Audit

- Date: 11/04/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0005.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0005/pass` reports `pass · all rules`, and `--path examples/HL-0005/fail` reports R-005.
