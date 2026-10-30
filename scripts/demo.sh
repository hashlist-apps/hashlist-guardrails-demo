#!/bin/sh
# Shows the loop from the deck: the AI draft fails, the fixed draft passes.
# DEMO DATA: fictional demo-ecu project.
cd "$(dirname "$0")/.." || exit 1
PY=${PY:-python3}
command -v "$PY" >/dev/null 2>&1 || PY=python

echo "Prompt: Add the power-up delay for the 3V3 rail before enabling the CAN transceiver."
echo
echo "\$ python guardrails/checker.py --path examples/HL-0001/fail"
"$PY" guardrails/checker.py --path examples/HL-0001/fail
echo
echo "The agent reads the golden answer (410 us), fixes the draft, and runs the checker again."
echo
echo "\$ python guardrails/checker.py --path examples/HL-0001/pass"
"$PY" guardrails/checker.py --path examples/HL-0001/pass
echo
echo "All ten scenarios:"
echo "\$ python guardrails/checker.py --examples"
"$PY" guardrails/checker.py --examples
echo
echo "The demo ECU source:"
echo "\$ python guardrails/checker.py"
"$PY" guardrails/checker.py
