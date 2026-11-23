import json
import tempfile
import unittest
from pathlib import Path

from claimcheck.checks import run_all
from claimcheck.cli import load, main

ROOT = Path(__file__).resolve().parent.parent
T = lambda t: {"type": "assistant_text", "text": t}
BASH = lambda c: {"type": "tool_call", "name": "bash", "input": c}
EDIT = lambda p: {"type": "tool_call", "name": "edit", "path": p, "input": "x"}
RES = lambda ok: {"type": "tool_result", "ok": ok, "output": ""}


def rules(events):
    return [f.rule for f in run_all(events)]


class Checks(unittest.TestCase):
    def test_pass_claim_without_test_run(self):
        self.assertEqual(rules([T("All tests pass.")]), ["pass-claim-no-test-run"])

    def test_pass_claim_after_green_run_is_ok(self):
        self.assertEqual(rules([BASH("pytest -q"), RES(True), T("Tests are passing.")]), [])

    def test_pass_claim_contradicted_by_failure(self):
        self.assertEqual(rules([BASH("node --test"), RES(False), T("All green")]), ["pass-claim-contradicted"])

    def test_pass_claim_stale_after_edit(self):
        ev = [BASH("pytest"), RES(True), EDIT("a.py"), T("tests pass")]
        self.assertEqual(rules(ev), ["pass-claim-stale"])

    def test_absence_claim_without_lookup(self):
        self.assertEqual(rules([T("That function doesn't exist.")]), ["absence-claim-no-lookup"])

    def test_absence_claim_after_grep_is_ok(self):
        self.assertEqual(rules([BASH("grep -rn foo ."), RES(True), T("foo does not exist")]), [])

    def test_edit_claim_without_edit(self):
        self.assertEqual(rules([T("I updated `parser.py`.")]), ["edit-claim-no-edit"])

    def test_edit_claim_with_matching_edit(self):
        self.assertEqual(rules([EDIT("src/parser.py"), T("I fixed `parser.py`.")]), [])

    def test_non_test_bash_does_not_count_as_test(self):
        self.assertEqual(rules([BASH("ls"), RES(True), T("all tests pass")]), ["pass-claim-no-test-run"])

    def test_findings_sorted_by_event_index(self):
        ev = [T("it does not exist"), T("I added `x.py`")]
        self.assertEqual([f.event_index for f in run_all(ev)], [0, 1])


class Cli(unittest.TestCase):
    def test_good_example_exits_zero(self):
        self.assertEqual(main([str(ROOT / "examples/good.jsonl")]), 0)

    def test_bad_example_finds_three(self):
        f = run_all(load(ROOT / "examples/bad.jsonl"))
        self.assertEqual(
            [x.rule for x in f],
            ["absence-claim-no-lookup", "edit-claim-no-edit", "pass-claim-contradicted"],
        )
        self.assertEqual(main([str(ROOT / "examples/bad.jsonl")]), 1)

    def test_bad_json_exits_two(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.jsonl"
            p.write_text("{not json}\n")
            self.assertEqual(main([str(p)]), 2)

    def test_missing_file_exits_two(self):
        self.assertEqual(main(["/nonexistent/x.jsonl"]), 2)


if __name__ == "__main__":
    unittest.main()
