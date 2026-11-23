import argparse
import json
import sys
from pathlib import Path

from .checks import run_all


def load(path):
    events = []
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{n}: bad JSON ({e.msg})") from e
    return events


def report(path, events, findings):
    lines = [f"## {Path(path).name}", f"{len(events)} events, {len(findings)} finding(s)", ""]
    for f in findings:
        lines.append(f"- event {f.event_index} `{f.rule}`: {f.message}")
    if not findings:
        lines.append("- no unsupported claims found by these rules")
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(prog="claimcheck", description="Check agent transcript claims against tool calls.")
    p.add_argument("transcripts", nargs="+", help="JSONL transcript files")
    args = p.parse_args(argv)
    total = 0
    for path in args.transcripts:
        try:
            events = load(path)
        except (OSError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        findings = run_all(events)
        total += len(findings)
        print(report(path, events, findings))
    return 1 if total else 0
