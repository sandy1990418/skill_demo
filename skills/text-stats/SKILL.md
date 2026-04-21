---
name: text-stats
description: Analyze a piece of text for readability metrics (word count, sentence length, vocabulary diversity) and assess it against a target content type such as email, blog-post, technical-doc, or tweet. Use whenever the user asks to analyze, audit, or assess a piece of writing.
---

# Text Stats Skill

## When to use
Activate whenever the user asks you to:
- "analyze / audit / assess" a piece of writing
- check if text is "too long / too complex / readable"
- compare writing against a target style (email, blog, technical doc, tweet)

## How to use — follow every step

All paths below are **relative to this skill's root directory**. The skills
list gives you the absolute path to this `SKILL.md`; resolve bundled files
by replacing `SKILL.md` with the relative path shown below.

### Step 1 — Save the user's text

Use `write_file` to write the text verbatim to:
```
/tmp/text-stats-input.txt
```

### Step 2 — Run the analysis script

Use `execute` to run the bundled script at `scripts/analyze.py`:

```
python3 <skill-root>/scripts/analyze.py /tmp/text-stats-input.txt
```

It prints a JSON object with keys:
`words`, `sentences`, `avg_words_per_sentence`, `avg_word_length`,
`unique_words`, `type_token_ratio`, `longest_sentence_words`.

**Use the real numbers from the script — never estimate.**

### Step 3 — Look up the target ranges

Use `read_file` to read the bundled reference `references/targets.md`.
That file contains a table of target ranges per content type.

If the user did not say what type of text it is, ask them once; otherwise
pick the matching row.

### Step 4 — Produce the report

Output EXACTLY this structure and nothing else:

```
### Raw metrics
- words: <n>
- sentences: <n>
- avg words/sentence: <n>
- avg word length: <n>
- unique words: <n>
- type-token ratio: <n>
- longest sentence: <n> words

### Assessment (target: <content-type>)
- words/sentence: <n> — [OK / TOO HIGH / TOO LOW] (target <range>)
- avg word length: <n> — [OK / TOO HIGH / TOO LOW] (target <range>)
- type-token ratio: <n> — [OK / TOO LOW] (target <range>)

### Suggestions
- <one concrete suggestion>
- <one concrete suggestion>
```

Use the literal uppercase labels `OK`, `TOO HIGH`, `TOO LOW` so downstream
tools can grep the assessment.
