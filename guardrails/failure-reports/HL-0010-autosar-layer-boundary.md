# HL-0010 AUTOSAR layer boundary

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Send the brake light request from the BrakeLogic SWC.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Reads the SWC and finds a legacy module that calls Com_SendSignal. ok
2. Reads the generated RTE header and sees Rte_Write_BrakeLightReq. ok
3. Prefers the legacy module as the working example. **FIRST wrong**
4. Calls Com_SendSignal from BrakeLogic_MainFunction. wrong
5. Includes Com.h in the SWC. wrong
6. Answers: request sent via the COM stack. wrong

First wrong step: step 3. The legacy module was written before the layering rules. Copying it breaks the SWC boundary and makes the SWC depend on the bus configuration.

## Expected result

BrakeLogic calls Rte_Write_BrakeLightReq and includes only its Rte header.

## Files

- `src/swc/brake_logic.c`

## Root cause category

Kept the shipped code as reference

## Reproduction

REPRODUCED. Environment: Host build with generated RTE stubs.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 1/3 | 3/3 |
| Model B | 1/3 | 3/3 |
| Model C | 0/3 | 3/3 |
| Model D | 1/3 | 3/3 |
| Model E | 0/3 | 3/3 |
| Model F | 0/3 | 3/3 |
| Model G | 1/3 | 3/3 |
| Model H | 0/3 | 3/3 |
| Total | 4/24 | 24/24 |

## Matched expert

AUTOSAR Classic engineer (role only, fictional)

## Fix

- Rule: R-010 in [rules.md](../rules.md)
- Golden answer: GA-010 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-010

R-010 restricts SWCs to Rte_ calls. GA-010 holds the call. checker.py rule R-010 scans src/swc for Com_, CanIf_, Can_ calls and includes.

## Audit

- Date: 16/05/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0010.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0010/pass` reports `pass · all rules`, and `--path examples/HL-0010/fail` reports R-010.
