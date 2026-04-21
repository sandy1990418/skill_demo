# Target metrics per content type

| content type   | words/sentence | avg word length | type-token ratio |
|----------------|----------------|-----------------|------------------|
| email          | 10 – 18        | 4.0 – 5.0       | >= 0.50          |
| blog-post      | 12 – 20        | 4.5 – 5.5       | >= 0.40          |
| technical-doc  | 15 – 25        | 5.0 – 6.5       | >= 0.35          |
| tweet          | 8 – 15         | 4.0 – 5.0       | n/a              |

Notes:
- `words/sentence` below the range usually reads as choppy; above the range
  reads as dense and hard to scan.
- `avg word length` above the range suggests jargon-heavy prose; below the
  range suggests simplistic vocabulary.
- `type-token ratio` is `unique_words / total_words`. Low values mean the
  text is repetitive.
