#!/usr/bin/env python3
"""
Content Review - Stop hook for claude-content-engine.

Runs when Claude is about to finish a response. Checks the transcript
for any content that was generated during this turn and flags quality
issues, ensuring Claude self-corrects before the conversation ends.

This is a lightweight final pass - the heavy lifting is done by
quality_gate.py on each write operation.
"""

import json
import sys


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Don't block stopping on errors
        print(json.dumps({"decision": "approve"}))
        return

    # Approve stopping - this hook is advisory, not blocking.
    # It provides a final reminder to Claude to review quality.
    output = {
        "decision": "approve",
        "systemMessage": (
            "Before finalizing: scan your response for AI-sounding phrases "
            "(delve, tapestry, leverage, seamlessly, in today's fast-paced world, "
            "it's important to note, game-changer, etc.). "
            "If any are present, rewrite those sections to sound human."
        )
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
