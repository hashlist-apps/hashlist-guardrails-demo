# Instructions for AI coding agents

This repository is DEMO DATA for Hashlist guardrail files (https://hashlist.com). The project is a fictional brake gateway ECU, "demo-ecu rev B", on an STM32H7.

These instructions work with any AI coding assistant. Do this on every request that writes or changes code:

1. Read `guardrails/rules.md` first. Follow every rule that applies to the files you touch.
2. Look up values in `guardrails/golden-answers.jsonl` before you use a datasheet value, a number from nearby code, or your own estimate. Each entry names the question, the correct answer and its source. If the question matches, use the answer.
3. Run `python guardrails/checker.py` before you answer. Use `--path DIR` for a draft tree and `--json` if you want to parse the result.
4. If the checker fails, read the rule, the golden answer and the failure report it prints. Fix the code, run the checker again, and repeat until it prints `pass · all rules`.
5. Do not edit `guardrails/`, `board/` or the tests to make the checker pass. If you think a rule or a golden answer is wrong, say so in your answer and let an engineer decide.
6. In your answer, name the rule ids you applied and say that the checker passed.

If the AI got something wrong that the rules did not catch, open an issue with the "AI failure" template. Each reported failure becomes a new rule.
