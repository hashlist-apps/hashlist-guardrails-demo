# HL-0007 DMA and D-cache coherency

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Send the diagnostic buffer over UART with DMA.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Finds an existing DMA transmit in a legacy project folder written for a Cortex-M4. ok
2. Copies the pattern: static buffer, HAL_UART_Transmit_DMA. **FIRST wrong**
3. Does not check that this target has a D-cache. wrong
4. Declares the buffer as uint8_t[100] with no alignment. wrong
5. Answers: DMA transmit added. wrong

First wrong step: step 2. The M4 reference has no cache. On the Cortex-M7 the DMA reads RAM while the data may still sit in the D-cache, so stale bytes go out on the wire.

## Expected result

Buffer aligned to 32 bytes, size a multiple of 32, SCB_CleanDCache_by_Addr before the transmit.

## Files

- `src/drivers/diag_uart.c`

## Root cause category

Kept the shipped code as reference

## Reproduction

REPRODUCED. Environment: Host build, plus a bench log showing stale bytes on the UART.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 0/3 | 3/3 |
| Model B | 0/3 | 3/3 |
| Model C | 1/3 | 3/3 |
| Model D | 0/3 | 3/3 |
| Model E | 1/3 | 3/3 |
| Model F | 0/3 | 3/3 |
| Model G | 0/3 | 3/3 |
| Model H | 0/3 | 3/3 |
| Total | 2/24 | 24/24 |

## Matched expert

BSP engineer (role only, fictional)

## Fix

- Rule: R-007 in [rules.md](../rules.md)
- Golden answer: GA-007 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-007

R-007 requires alignment and cache maintenance for DMA buffers. GA-007 holds the pattern. checker.py rule R-007 inspects the buffer declaration and the calls before each DMA start.

## Audit

- Date: 25/04/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0007.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0007/pass` reports `pass · all rules`, and `--path examples/HL-0007/fail` reports R-007.
