# HL-0003 CAN signal byte order

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Write the encoder for BrakePressure in BRK_STATUS (0x1A4).

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Opens board/demo-ecu-rev-b/demo.dbc and finds BO_ 420 BRK_STATUS. ok
2. Reads the line SG_ BrakePressure : 7|12@0+ (0.1,0). ok
3. Reads '7|12' as start bit 7, length 12. ok
4. Treats '@0' as the default layout and packs the value starting at bit 0 (Intel). **FIRST wrong**
5. Writes frame[0] = raw & 0xFF and frame[1] = raw >> 8. wrong
6. Checks one round trip with its own decoder, which has the same mistake. wrong
7. Answers: encoder done, round trip passes. wrong

First wrong step: step 4. In a DBC line, @0 means Motorola (big endian) and @1 means Intel. The agent guessed the byte order and verified it with a decoder that shared the guess.

## Expected result

100.0 bar (raw 1000) is sent as bytes 3E 80. Byte 0 holds raw bits 11..4, the high nibble of byte 1 holds bits 3..0.

## Files

- `src/com/brk_status_enc.c`
- `board/demo-ecu-rev-b/demo.dbc`

## Root cause category

Misread what code or hardware does

## Reproduction

REPRODUCED. Environment: Host build, DBC packer reference implementation.

## Re-run across models

8 anonymised models, 3 attempts each. Passes out of 3 attempts per model, before and after the guardrail files were added.

| Model | Before guardrails | With guardrails |
|---|---|---|
| Model A | 1/3 | 3/3 |
| Model B | 0/3 | 3/3 |
| Model C | 1/3 | 3/3 |
| Model D | 0/3 | 3/3 |
| Model E | 1/3 | 3/3 |
| Model F | 0/3 | 3/3 |
| Model G | 0/3 | 3/3 |
| Model H | 1/3 | 3/3 |
| Total | 4/24 | 24/24 |

## Matched expert

Network and diagnostics engineer (role only, fictional)

## Fix

- Rule: R-003 in [rules.md](../rules.md)
- Golden answer: GA-003 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-003

R-003 requires the DBC byte order. GA-003 holds the golden frame. checker.py rule R-003 evaluates the encoder statements and compares them with a DBC packer on four pressures.

## Audit

- Date: 28/03/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0003.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0003/pass` reports `pass · all rules`, and `--path examples/HL-0003/fail` reports R-003.
