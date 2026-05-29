---
name: use-interview-tool
description: Use when explicitly asked to present clarifying questions via the pi-interview-tool interactive UI instead of chat.
---

Present questions via the pi-interview-tool UI instead of printing them in chat.

## Steps

**1. Write questions JSON to a temp file:**

```bash
TMPFILE=$(mktemp /tmp/interview-XXXXXX.json)
cat > "$TMPFILE" << 'ENDJSON'
{
  "title": "<topic>",
  "description": "<brief context>",
  "questions": [
    {
      "id": "q1",
      "type": "single",
      "question": "Which approach?",
      "options": ["Option A", "Option B"],
      "recommended": "Option A",
      "conviction": "strong",
      "context": "Why this matters"
    },
    {
      "id": "q2",
      "type": "text",
      "question": "What is the primary goal?"
    },
    {
      "id": "q3",
      "type": "multi",
      "question": "Which constraints apply?",
      "options": ["Performance", "Cost", "Maintainability"],
      "recommended": ["Performance"]
    }
  ]
}
ENDJSON
```

Types: `single` (radio), `multi` (checkboxes), `text` (freeform), `info` (read-only panel)
Fields: `recommended` (label string or array), `conviction` (`"strong"|"slight"`), `weight` (`"critical"|"minor"`), `context` (shown below question)

**2. Launch and wait:**

```bash
bun /Users/aisarva/Downloads/pi-interview-tool/interview-cli.ts "$TMPFILE" --title="<topic>"
```

Opens native macOS Glimpse window or browser tab. Blocks until user submits.

**3. Parse stdout response:**

```json
{
  "status": "submitted",
  "responses": [
    { "questionId": "q1", "value": "Option A" },
    { "questionId": "q2", "value": "Build a service mesh" },
    { "questionId": "q3", "value": ["Performance", "Maintainability"] }
  ]
}
```

Batch related decisions into one round — don't open the tool for a single question.
