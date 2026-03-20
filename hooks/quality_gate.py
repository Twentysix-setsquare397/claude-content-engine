#!/usr/bin/env python3
"""
Content Quality Gate - PostToolUse hook for claude-content-engine.

Scans written content for AI slop patterns, cliches, weak copy,
and common low-effort writing. Sends feedback to Claude so it
can self-correct before the user sees the final output.

This hook runs after Write/Edit operations on content files
(markdown, text, etc.) - not on code files.
"""

import json
import sys
import os
import re

# File extensions that contain written content (not code)
CONTENT_EXTENSIONS = {
    ".md", ".mdx", ".txt", ".html", ".htm",
}

# Extensions to skip entirely (code, config, binary)
SKIP_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".css", ".scss",
    ".sh", ".bash", ".zsh", ".fish",
    ".go", ".rs", ".rb", ".java", ".c", ".cpp", ".h",
    ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".lock", ".sum", ".mod",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz",
}

# --- AI slop patterns ---
# These are phrases that almost always signal lazy AI-generated text.
# Organized by severity.

HARD_SLOP = [
    # Words/phrases that are dead giveaways
    r"\bdelve\b",
    r"\btapestry\b",
    r"\bunlock the power\b",
    r"\bin today'?s (?:fast-paced|ever-changing|digital|modern) (?:world|landscape|era|age)\b",
    r"\bit'?s important to note\b",
    r"\bit'?s worth noting\b",
    r"\bin the realm of\b",
    r"\bgame[ -]?changer\b",
    r"\bparadigm shift\b",
    r"\bsynergy\b",
    r"\bholistic approach\b",
    r"\bseamless(?:ly)?\b",
    r"\bleverage\b(?! (?:ratio|point))",  # allow financial usage
    r"\brobust\b(?! (?:error|test|check))",  # allow technical usage
    r"\bcut(?:ting)?[ -]?edge\b",
    r"\binnovative solution\b",
    r"\bempowering\b",
    r"\btransformative\b",
    r"\bgroundbreaking\b",
    r"\brevolutionize\b",
    r"\bworld-class\b",
    r"\bnot just .+? but (?:also )?.+? it'?s\b",
    r"\bwhether you'?re .+? or .+?,\b",
    r"\bfrom .+? to .+?, we'?ve got you covered\b",
]

SOFT_SLOP = [
    # Phrases that are sometimes fine but often signal AI filler
    r"\bin conclusion\b",
    r"\bas we'?ve (?:seen|discussed|explored)\b",
    r"\blet'?s (?:dive|explore|unpack)\b",
    r"\bwithout further ado\b",
    r"\bin this (?:article|blog post|guide|piece)\b",
    r"\bhope this (?:helps|was helpful|article)\b",
    r"\bthe (?:landscape|world) of\b",
    r"\bnavigat(?:e|ing) the\b",
    r"\bharnessing?\b",
    r"\bfoster(?:ing)?\b",
    r"\bpivotal\b",
    r"\bmyriad\b",
    r"\bplethora\b",
    r"\bcommence\b",
    r"\butilize\b",
    r"\bfacilitate\b",
]

# --- Weak copy patterns ---
WEAK_PATTERNS = [
    (r"\bvery (?:good|nice|great|important|big|small)\b", "Replace 'very + weak adjective' with a stronger word"),
    (r"\breally (?:good|nice|great|important)\b", "Replace 'really + weak adjective' with a stronger word"),
    (r"\b(?:I|we) (?:think|believe|feel) that\b", "Cut the hedge - just state the claim"),
    (r"\bin order to\b", "Replace 'in order to' with 'to'"),
    (r"\bdue to the fact that\b", "Replace 'due to the fact that' with 'because'"),
    (r"\bat the end of the day\b", "Cliche - cut or replace"),
    (r"\bmoving forward\b", "Corporate filler - cut it"),
    (r"\bneedless to say\b", "If it's needless, don't say it"),
    (r"\bit goes without saying\b", "Then don't say it"),
]


def get_file_extension(filepath):
    """Extract file extension, lowercased."""
    if not filepath:
        return ""
    _, ext = os.path.splitext(filepath)
    return ext.lower()


def should_scan(filepath):
    """Determine if this file should be scanned for content quality."""
    ext = get_file_extension(filepath)
    if ext in SKIP_EXTENSIONS:
        return False
    if ext in CONTENT_EXTENSIONS:
        return True
    # Unknown extension - skip to avoid false positives
    return False


def scan_content(text):
    """Scan text for quality issues. Returns a list of findings."""
    findings = []

    if not text or len(text.strip()) < 50:
        return findings

    text_lower = text.lower()

    # Check hard slop
    for pattern in HARD_SLOP:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            match_text = matches[0] if isinstance(matches[0], str) else matches[0][0]
            findings.append({
                "severity": "high",
                "type": "ai_slop",
                "match": match_text.strip(),
                "suggestion": f"Remove or rewrite: '{match_text.strip()}' is a common AI-generated filler phrase."
            })

    # Check soft slop (only flag if 2+ found)
    soft_matches = []
    for pattern in SOFT_SLOP:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            match_text = matches[0] if isinstance(matches[0], str) else matches[0][0]
            soft_matches.append(match_text.strip())

    if len(soft_matches) >= 2:
        findings.append({
            "severity": "medium",
            "type": "ai_pattern",
            "match": ", ".join(soft_matches[:5]),
            "suggestion": f"Multiple AI-sounding phrases detected: {', '.join(soft_matches[:5])}. Rewrite to sound more natural."
        })

    # Check weak patterns
    for pattern, suggestion in WEAK_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            match_text = matches[0] if isinstance(matches[0], str) else matches[0][0]
            findings.append({
                "severity": "low",
                "type": "weak_copy",
                "match": match_text.strip(),
                "suggestion": suggestion
            })

    # Check for excessive exclamation marks (sign of fake enthusiasm)
    exclamation_count = text.count("!")
    sentence_count = max(len(re.split(r'[.!?]+', text)) - 1, 1)
    if exclamation_count > 3 and exclamation_count / sentence_count > 0.3:
        findings.append({
            "severity": "medium",
            "type": "tone",
            "match": f"{exclamation_count} exclamation marks in {sentence_count} sentences",
            "suggestion": "Too many exclamation marks - reads as fake enthusiasm. Keep to 1-2 per piece max."
        })

    return findings


def format_findings(findings):
    """Format findings into a system message for Claude."""
    if not findings:
        return None

    high = [f for f in findings if f["severity"] == "high"]
    medium = [f for f in findings if f["severity"] == "medium"]
    low = [f for f in findings if f["severity"] == "low"]

    parts = ["**Content Quality Gate - issues detected:**\n"]

    if high:
        parts.append("**Must fix (AI slop detected):**")
        for f in high:
            parts.append(f"- `{f['match']}` - {f['suggestion']}")
        parts.append("")

    if medium:
        parts.append("**Should fix:**")
        for f in medium:
            parts.append(f"- `{f['match']}` - {f['suggestion']}")
        parts.append("")

    if low:
        parts.append("**Consider fixing:**")
        for f in low:
            parts.append(f"- `{f['match']}` - {f['suggestion']}")
        parts.append("")

    parts.append("Rewrite the flagged sections before presenting to the user. Do not mention this review.")

    return "\n".join(parts)


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({}))
        return

    tool_input = hook_input.get("tool_input", {})
    tool_result = hook_input.get("tool_result", "")

    # Determine the file path
    filepath = tool_input.get("file_path", tool_input.get("path", ""))

    if not filepath or not should_scan(filepath):
        print(json.dumps({}))
        return

    # Get the content that was written
    content = tool_input.get("content", "")  # Write tool
    if not content:
        content = tool_input.get("new_string", "")  # Edit tool
    if not content:
        content = tool_input.get("new_source", "")  # NotebookEdit

    if not content:
        print(json.dumps({}))
        return

    findings = scan_content(content)
    message = format_findings(findings)

    if message:
        output = {
            "systemMessage": message,
            "suppressOutput": False,
            "continue": True
        }
    else:
        output = {}

    print(json.dumps(output))


if __name__ == "__main__":
    main()
