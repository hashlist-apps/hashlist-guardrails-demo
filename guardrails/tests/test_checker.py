"""Tests for guardrails/checker.py. Standard library only: python -m unittest discover -s guardrails/tests"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "guardrails"))
import checker  # noqa: E402

CLI = [sys.executable, str(REPO / "guardrails" / "checker.py")]
SCENARIOS = sorted(p.name for p in (REPO / "examples").glob("HL-*"))


def rules_for(path):
    return sorted({f.rule for f in checker.run_rules(checker.Tree(path))})


class ScenarioTests(unittest.TestCase):
    def test_ten_scenarios(self):
        self.assertEqual(len(SCENARIOS), 10)

    def test_fail_drafts_fail_only_their_rule(self):
        for ex in SCENARIOS:
            with self.subTest(ex):
                rule = f"R-{int(ex.split('-')[1]):03d}"
                self.assertEqual(rules_for(REPO / "examples" / ex / "fail"), [rule])

    def test_pass_drafts_pass(self):
        for ex in SCENARIOS:
            with self.subTest(ex):
                self.assertEqual(rules_for(REPO / "examples" / ex / "pass"), [])

    def test_src_passes_all_rules(self):
        self.assertEqual(rules_for(REPO / "src"), [])

    def test_src_is_union_of_pass_drafts(self):
        for ex in SCENARIOS:
            for p in (REPO / "examples" / ex / "pass").rglob("*"):
                if p.is_file():
                    rel = p.relative_to(REPO / "examples" / ex / "pass")
                    self.assertEqual((REPO / rel).read_text(), p.read_text(), str(rel))


class RuleDetailTests(unittest.TestCase):
    def test_r001_message_names_both_values(self):
        f = checker.run_rules(checker.Tree(REPO / "examples/HL-0001/fail"))
        msgs = " ".join(x.message for x in f)
        self.assertIn("230", msgs)
        self.assertIn("410", msgs)
        self.assertTrue(any(x.file.startswith("test/") for x in f), "the self-referencing test is flagged")

    def test_r002_error_is_above_one_percent(self):
        f = checker.run_rules(checker.Tree(REPO / "examples/HL-0002/fail"))
        self.assertIn("1.20%", f[0].message)

    def test_r003_golden_frame(self):
        sig = checker.load_dbc_signal("BrakePressure")
        data, _ = checker.dbc_pack(sig, 1000)
        self.assertEqual(data[:2], [0x3E, 0x80])

    def test_r004_crc_check_value(self):
        self.assertEqual(checker.crc8(b"123456789", 0x1D, 0xFF, 0xFF), 0x4B)
        self.assertNotEqual(checker.crc8(b"123456789", 0x07, 0x00, 0x00), 0x4B)

    def test_r005_flags_both_problems(self):
        f = checker.run_rules(checker.Tree(REPO / "examples/HL-0005/fail"))
        self.assertEqual(len(f), 2)

    def test_r006_lists_each_forbidden_call(self):
        f = checker.run_rules(checker.Tree(REPO / "examples/HL-0006/fail"))
        calls = {re.match(r"(\w+)\(", x.message).group(1) for x in f}
        self.assertEqual(calls, {"printf", "xQueueSend", "HAL_Delay"})

    def test_r006_allows_fromisr_variant(self):
        self.assertEqual(rules_for(REPO / "examples/HL-0006/pass"), [])

    def test_r008_refresh_outside_function(self):
        f = checker.run_rules(checker.Tree(REPO / "examples/HL-0008/fail"))
        self.assertIn("SysTick_Handler", f[0].message)

    def test_comments_do_not_trigger(self):
        src = checker.Src("src/x.c", "/* malloc(1) */ // free(p)\nint a;\n")
        self.assertNotIn("malloc", src.text)
        self.assertNotIn("free", src.text)

    def test_c_eval(self):
        self.assertAlmostEqual(checker.c_eval("0.01 * 100.0 / 101.2"), 0.009881422924901186)
        self.assertEqual(checker.c_eval("(uint8_t)((raw & 0x0Fu) << 4)", {"raw": 0x3E8}), 0x80)
        with self.assertRaises(checker.CEvalError):
            checker.c_eval("__import__('os')")


class DataFileTests(unittest.TestCase):
    def setUp(self):
        self.golden = [json.loads(x) for x in (REPO / "guardrails/golden-answers.jsonl").read_text().splitlines()]
        self.rules_md = (REPO / "guardrails/rules.md").read_text()

    def test_golden_fields(self):
        need = {"id", "rule", "question", "answer", "source", "not", "applies_to", "verified_by", "failure_report"}
        self.assertEqual(len(self.golden), 10)
        for g in self.golden:
            self.assertTrue(need <= set(g), g["id"])

    def test_every_rule_links_report_and_golden(self):
        for g in self.golden:
            block = self.rules_md.split(f"## {g['rule']} ")[1].split("\n## ")[0]
            self.assertIn(f"Golden answers: {g['id']}", block)
            reports = list((REPO / "guardrails/failure-reports").glob(f"{g['failure_report']}-*.md"))
            self.assertEqual(len(reports), 1, g["failure_report"])
            self.assertIn(f"failure-reports/{reports[0].name}", block)
            self.assertTrue((REPO / "guardrails/prompts" / f"{g['failure_report']}.prompt.md").exists())

    def test_reports_have_required_sections(self):
        sections = ["Prompt", "Agent trace", "Expected result", "Files", "Root cause category", "Reproduction",
                    "Re-run across models", "Matched expert", "Fix", "Audit"]
        cats = {"Trusted a document over the data", "Kept the shipped code as reference",
                "Misread what code or hardware does"}
        for p in (REPO / "guardrails/failure-reports").glob("HL-*.md"):
            text = p.read_text()
            for s in sections:
                self.assertIn(f"## {s}", text, p.name)
            self.assertEqual(text.count("**FIRST wrong**"), 1, p.name)
            self.assertTrue(any(c in text for c in cats), p.name)
            self.assertRegex(text, r"Date: \d\d/\d\d/\d{4}")

    def test_rule_table_matches_checker(self):
        for rid in checker.RULES:
            self.assertIn(f"## {rid} ", self.rules_md)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(CLI + list(args), capture_output=True, text=True, encoding="utf-8", cwd=REPO)

    def test_default_passes(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0)
        self.assertIn("pass · all rules", r.stdout)

    def test_failing_draft_exit_1_and_names_report(self):
        r = self.run_cli("--path", "examples/HL-0001/fail")
        self.assertEqual(r.returncode, 1)
        self.assertIn("R-001 fail", r.stdout)
        self.assertIn("HL-0001-pmic-settle-time.md", r.stdout)
        self.assertIn("golden GA-001: 410 us", r.stdout)

    def test_json(self):
        r = self.run_cli("--json", "--path", "examples/HL-0003/fail")
        data = json.loads(r.stdout)
        self.assertEqual(data["status"], "fail")
        self.assertEqual(data["findings"][0]["golden_answer"]["id"], "GA-003")

    def test_ci_annotations(self):
        r = self.run_cli("--ci", "--path", "examples/HL-0009/fail")
        self.assertEqual(r.returncode, 1)
        self.assertRegex(r.stdout, r"::error file=examples/HL-0009/fail/src/diag/dtc_store\.c,line=\d+,title=R-009")
        self.assertIn("| Rule |", r.stdout)

    def test_examples_mode(self):
        r = self.run_cli("--examples")
        self.assertEqual(r.returncode, 0)
        self.assertIn("10 of 10", r.stdout)

    def test_root_entry_point(self):
        r = subprocess.run([sys.executable, str(REPO / "checker.py")], capture_output=True, text=True,
                           encoding="utf-8", cwd=REPO)
        self.assertEqual(r.returncode, 0)


class AssetTests(unittest.TestCase):
    def test_svgs_are_valid_and_self_contained(self):
        import xml.etree.ElementTree as ET
        svgs = sorted((REPO / "assets").glob("*.svg"))
        self.assertGreaterEqual(len(svgs), 2)
        for p in svgs:
            text = p.read_text(encoding="utf-8")
            root = ET.fromstring(text)
            self.assertTrue(root.tag.endswith("svg"), p.name)
            self.assertIn("@keyframes", text, p.name)
            self.assertIn("prefers-reduced-motion", text, p.name)
            self.assertNotIn("<script", text, p.name)
            self.assertNotIn("http://", text.replace("http://www.w3.org/2000/svg", ""), p.name)
            self.assertNotIn("href=", text, p.name)

    def test_catch_animation_shows_real_checker_output(self):
        text = (REPO / "assets" / "checker-catch.svg").read_text(encoding="utf-8")
        r = subprocess.run(CLI + ["--path", "examples/HL-0001/fail"], capture_output=True, text=True,
                           encoding="utf-8", cwd=REPO)
        first = r.stdout.splitlines()[0].split("checker.py", 1)[1].strip()
        self.assertIn(first.split(" (see")[0].replace("&", "&amp;"), text)


class RepoHygieneTests(unittest.TestCase):
    def test_no_em_dashes_or_emoji(self):
        for p in REPO.rglob("*"):
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts and p.suffix not in (".png", ".gif"):
                text = p.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn(chr(0x2014), text, str(p))
                self.assertFalse(re.search("[" + chr(0x1F300) + "-" + chr(0x1FAFF) + chr(0x2600) + "-" + chr(0x27BF) + "]", text), str(p))

    def test_no_forbidden_words(self):
        banned = ["honda", "toyota", "bmw", "openai", "anthropic", "gemini", "claude-", "usd", "$"]
        for p in REPO.rglob("*"):
            if p.is_file() and ".git" not in p.parts and p.suffix == ".md" and p.name != "AGENTS.md":
                low = p.read_text(encoding="utf-8").lower()
                for b in banned[:6]:
                    self.assertNotIn(b, low, f"{b} in {p}")


if __name__ == "__main__":
    unittest.main()
