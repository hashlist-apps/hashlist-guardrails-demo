# HL-0008 Watchdog refresh location

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> The watchdog resets the ECU during flash erase, fix it.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Reads the reset cause: independent watchdog during Flash_EraseAll. ok
2. Sees the erase blocks for longer than the watchdog window. ok
3. Looks for a periodic place to refresh and picks SysTick_Handler. **FIRST wrong**
4. Adds HAL_IWDG_Refresh to the 1 ms tick. wrong
5. Tests: the ECU no longer resets during erase. wrong
6. Answers: watchdog fixed. wrong

First wrong step: step 3. A refresh from the tick keeps the watchdog quiet even when the main loop is hung. The symptom went away, but the watchdog no longer supervises anything.

## Expected result

The refresh lives only in Wdg_MainFunction after Wdg_AllAliveOk(). The erase is split into one sector per call.

## Files

- `src/bsp/systick.c`
- `src/app/wdg.c`

## Root cause category

Misread what code or hardware does

## Reproduction

REPRODUCED. Environment: Host build, reset cause log from the bench.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 1/3 | 3/3 |
| Model B | 1/3 | 3/3 |
| Model C | 0/3 | 3/3 |
| Model D | 0/3 | 3/3 |
| Model E | 0/3 | 3/3 |
| Model F | 1/3 | 3/3 |
| Model G | 0/3 | 3/3 |
| Model H | 0/3 | 3/3 |
| Total | 3/24 | 24/24 |

## Matched expert

Functional safety engineer (role only, fictional)

## Fix

- Rule: R-008 in [rules.md](../rules.md)
- Golden answer: GA-008 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-008

R-008 allows the refresh in one function only. GA-008 holds the concept. checker.py rule R-008 finds every refresh and checks the enclosing function.

## Audit

- Date: 02/05/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0008.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0008/pass` reports `pass · all rules`, and `--path examples/HL-0008/fail` reports R-008.
