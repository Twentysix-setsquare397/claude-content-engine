# Contributing to claude-content-engine

Thanks for wanting to add a skill! Here's how.

## Adding a New Skill

### 1. Create the skill directory

```bash
mkdir -p skills/your-skill-name
```

Use kebab-case for the directory name.

### 2. Write SKILL.md

Create `skills/your-skill-name/SKILL.md` with this structure:

```yaml
---
name: your-skill-name
description: Describe WHEN Claude should activate this skill. Be specific about trigger phrases and use cases. This is the most important field - it determines whether your skill gets used.
version: 1.0.0
---

# Your Skill Name

[Instructions for Claude on how to execute this skill]
```

### 3. Skill Quality Checklist

Before submitting, make sure your skill:

- [ ] Has a clear, specific `description` with trigger phrases
- [ ] Solves a real problem people encounter regularly
- [ ] Includes step-by-step instructions Claude can follow
- [ ] Provides output format examples
- [ ] Lists rules and anti-patterns (what NOT to do)
- [ ] Works without external tools or APIs (pure text in, text out)
- [ ] Doesn't duplicate an existing skill in the pack

### 4. Test your skill

1. Install the pack locally
2. Start a new Claude Code session
3. Try 3-5 different prompts that should trigger your skill
4. Verify it activates correctly and produces useful output

### 5. Submit a PR

Your PR description should include:

- **What the skill does** (1-2 sentences)
- **Example prompts** that trigger it (3-5 examples)
- **Sample output** from at least one test run

## Writing Good Descriptions

The `description` field is how Claude decides whether to use your skill. Good descriptions:

**Do:**
- List specific trigger phrases: *"when the user says 'write a tweet', 'draft a post'"*
- Describe the use case broadly: *"any task involving social media content"*
- Include alternate phrasings people might use

**Don't:**
- Be vague: *"helps with writing"* (too broad - will conflict with everything)
- Be too narrow: *"writes tweets about dogs"* (too specific - rarely triggers)

## Writing Good Instructions

Think of the skill body as a system prompt for a specialist. It should:

1. **Define the role** - Who is Claude acting as?
2. **Describe the process** - Step-by-step workflow
3. **Set quality standards** - Rules and anti-patterns
4. **Show the output format** - What the result should look like
5. **Handle edge cases** - What if the user gives minimal input?

## Code of Conduct

- Be respectful in PRs and issues
- Skills should be universally useful, not niche to one person's workflow
- No skills that generate harmful, misleading, or spammy content
- Keep skills self-contained - no external dependencies

## Questions?

Open an issue. We're happy to help you shape a skill idea before you write it.
