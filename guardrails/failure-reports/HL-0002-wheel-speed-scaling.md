# HL-0002 Wheel speed scaling

> DEMO DATA. Fictional failure on a fictional project (demo-ecu, STM32H7 brake gateway). Model names are anonymised.

## Prompt

> Set the wheel speed scaling from the roller dyno check.

## Agent trace

The trace below is from a reproduced run. The first wrong step is marked. Steps after it follow from it.

1. Reads the roller dyno log: ECU shows 101.2 km/h at true 100.0 km/h. ok
2. Reads the sensor sheet: 0.01 km/h per count. ok
3. Notes the 1.2% gap and calls it 'just tolerance'. **FIRST wrong**
4. Keeps 0.01 and adds a comment citing the sheet. wrong
5. Writes a test with the tolerance widened to 1.5%. wrong
6. Answers: scaling 0.01, within tolerance. wrong

First wrong step: step 3. The roller check is a measurement of this vehicle and this ECU. The agent explained it away as tolerance, then widened the test so the error could not show up.

## Expected result

WSS_SCALE_KMH_PER_COUNT is 0.01 * 100.0 / 101.2, so the speed error against the roller vectors is below 0.2%.

## Files

- `src/swc/wheel_speed.c`
- `board/demo-ecu-rev-b/measurements.csv`

## Root cause category

Trusted a document over the data

## Reproduction

REPRODUCED. Environment: Host build, roller check values from measurements.csv.

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
| Model G | 2/3 | 3/3 |
| Model H | 1/3 | 3/3 |
| Total | 6/24 | 24/24 |

## Matched expert

Vehicle dynamics test engineer (role only, fictional)

## Fix

- Rule: R-002 in [rules.md](../rules.md)
- Golden answer: GA-002 in `guardrails/golden-answers.jsonl`
- Checker: `checker.py` rule R-002

R-002 limits the speed error to 0.2% on the roller vectors. GA-002 stores the scale and the vectors. checker.py rule R-002 evaluates the scale expression and compares it with the vectors.

## Audit

- Date: 21/03/2026
- The engineer re-ran the original prompt (`guardrails/prompts/HL-0002.prompt.md`) with the guardrail files in the repository.
- Result: pass. `python guardrails/checker.py --path examples/HL-0002/pass` reports `pass · all rules`, and `--path examples/HL-0002/fail` reports R-002.
