# agent-claim-checker

Independent demo, not affiliated with G2i (cliente não diz).

When you judge a coding agent, the final message often says "all tests pass" or "I fixed `parser.py`". This small tool checks those sentences against what the agent did. It reads a transcript saved as JSONL and flags claims that its own tool calls do not support.

## Rules

- `pass-claim-no-test-run`: the agent says tests pass, but no test command ran.
- `pass-claim-stale`: tests passed once, then a file was edited, and the agent still says they pass.
- `pass-claim-contradicted`: the last test run failed, and the agent says it passed.
- `absence-claim-no-lookup`: the agent says something does not exist before any read or search.
- `edit-claim-no-edit`: the agent says it changed a file, but no edit call touched that file.

## Run it

Python 3.9 or newer, standard library only.

```
python -m claimcheck examples/good.jsonl examples/bad.jsonl
python -m unittest discover -s tests
```

Exit code 0 means no findings, 1 means findings, 2 means a file could not be read.

## Transcript format

One JSON object per line:

```
{"type": "assistant_text", "text": "I fixed `utils.py`."}
{"type": "tool_call", "name": "bash", "input": "pytest -q"}
{"type": "tool_call", "name": "edit", "path": "utils.py", "input": "..."}
{"type": "tool_result", "ok": false, "output": "2 failed"}
```

`name` is `bash`, `edit`, `read` or `search`. The two files in `examples/` are invented for this demo.

## What was tested

- 14 offline unit tests, run with `unittest` and in GitHub Actions. They cover each rule with a case that should fire and a case that should not, the sort order of findings, and the three exit codes.
- The two example transcripts give the expected findings (none for `good.jsonl`, three for `bad.jsonl`).

## What was not tested

- Real transcripts. I did not run it on output from Codex, Claude Code or Cursor, so I do not know how each tool names its calls. You would map them to the four `name` values.
- Accuracy. The rules are regular expressions on English text. They will miss claims phrased in other ways and may flag harmless sentences. I have not measured false positives or misses.
- Test commands outside the list in `claimcheck/checks.py` (pytest, unittest, npm test, node --test, go test, cargo test, rspec, mix test) are not recognised as test runs.
- It cannot judge whether a claim is true. It only checks that the transcript contains the action that would back it.
