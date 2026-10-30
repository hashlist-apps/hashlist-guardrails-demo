# Hashlist guardrails demo (fictional demo-ecu). Python 3.10+ standard library only.
PY ?= python3

.PHONY: check examples test demo all

check:      ## check src/ against the rules
	$(PY) guardrails/checker.py

examples:   ## every fail draft must fail, every pass draft must pass
	$(PY) guardrails/checker.py --examples

test:       ## unit tests
	$(PY) -m unittest discover -s guardrails/tests -v

demo:       ## show one fail then pass, step by step
	sh scripts/demo.sh

all: check examples test
