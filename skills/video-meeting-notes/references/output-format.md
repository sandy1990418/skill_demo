# Output markdown format

The composer must emit markdown that follows this structure exactly.

```markdown
# {{ derived title — short, content-based, NOT the filename }}

_Source: {{ filename }} · Duration: {{ mm:ss }} · Language: {{ lang }}_

## {{ Section 1 title }}

_{{ start_mm:ss }} – {{ end_mm:ss }}_

![scene](frames/frame_003.jpg)

- {{ key point }}
- {{ key point }}

## {{ Section 2 title }}

_{{ start_mm:ss }} – {{ end_mm:ss }}_

![scene](frames/frame_012.jpg)
![scene](frames/frame_018.jpg)

- {{ key point }}
- {{ key point }}
```

Rules:

1. The `# Title` line is generated from transcript content, not the filename.
2. The italic source line directly under the title — single line, three fields separated by ` · `.
3. Each `## Section` has:
   - heading
   - italic time range
   - 1+ image (relative path under `frames/`)
   - bulleted summary (3–6 bullets)
4. Sections are time-ordered.
5. If a section has no matching keyframe, omit the image — do NOT insert a placeholder.
6. Image paths are relative to the markdown file's location (i.e. just `frames/foo.jpg`).
