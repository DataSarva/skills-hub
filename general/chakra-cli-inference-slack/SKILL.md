---
name: chakra-cli-inference-slack
description: >
  The working model for running a chakra/hermes use-case agent (investsarva/instasarva/Chitti)
  on CC/Codex CLI inference behind Slack — WITHOUT a metered API. Covers the three hard-won
  mechanisms: (1) the CLI subprocess provider that drives `claude -p` / `codex exec` on the
  Mac's Keychain subscription auth, (2) the CommonMark→Slack mrkdwn converter so replies don't
  render raw `**bold**`, (3) the 👀→✅/❌ progress reactions + +1/-1 operator-approval gating.
  Read this before wiring any use-case agent to Slack, before touching a model provider, or
  when a Slack reply shows raw markdown / a reaction is missing / inference hits an API key
  instead of the subscription.
tier: general
tags: [chakra, hermes, slack, claude-cli, codex-cli, mrkdwn, reactions, subscription-auth, inference]
version: 1
---

# chakra-cli-inference-slack — CC/Codex CLI inference behind Slack

The model proven in production by **investsarva** + **instasarva**, preserved for the Option-D
rebuild (hermes kernel + CLI providers as plugins). Three mechanisms. All are upgrade-safe
**plugins/hooks**, never forks of upstream hermes.

> **Why CLI and not API?** We run on the *subscription* (Claude Max / ChatGPT-Codex), not a
> metered API key. The provider shells out to the same `claude` / `codex` binaries you use
> interactively, which authenticate via the macOS Keychain OAuth token. No `ANTHROPIC_API_KEY`.

---

## 1. The CLI subprocess provider (inference engine)

A hermes **model-provider plugin** that runs the CLI for ONE turn and streams text back. hermes
stays the agent (memory/context/tools); the CLI is just the model endpoint.

Source: `~/chakra/vendor/hermes/plugins/model-providers/{claude-code-cli,codex-cli}/provider.py`
→ in Option D these live in the clean hermes install's `plugins/model-providers/`.

### Exact invocation (copy these verbatim — the flags are load-bearing)

```python
# Claude. --verbose is MANDATORY: claude REFUSES -p + --output-format=stream-json without it.
argv = ["claude", "-p", "--verbose", "--output-format", "stream-json"]
if model_arg:                         # claude-opus-4-7 / claude-sonnet-4-6 / claude-haiku-4-5
    argv += ["--model", model_arg]
argv.append(prompt)

# Codex. Non-interactive exec mode, JSON event stream.
argv = ["codex", "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "--json", "--skip-git-repo-check"]
if model:
    argv += ["--model", model.strip()]
argv.append(prompt)
```

### The subscription-auth rule (this is THE gotcha)

Strip every Anthropic API env var from the subprocess env so the CLI falls back to its Keychain
subscription OAuth. If `ANTHROPIC_API_KEY` leaks in, you silently bill the metered API.

```python
SCRUBBED_ENV_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_TOKEN",
                     "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_KEY")
env = dict(os.environ)
for k in SCRUBBED_ENV_VARS:
    env.pop(k, None)
```

The launchd plist completes the picture — hydrate the Keychain token, unset the API vars
(the `slack-launcher.sh` pattern):

```bash
CLAUDE_CRED_JSON=$(/usr/bin/security find-generic-password -s "Claude Code-credentials" -a "$USER" -w)
export CLAUDE_CODE_OAUTH_TOKEN=$(python3 -c "import json,sys;print(json.loads(sys.argv[1])['claudeAiOauth']['accessToken'])" "$CLAUDE_CRED_JSON")
unset ANTHROPIC_API_KEY ANTHROPIC_TOKEN ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL ANTHROPIC_KEY
```

### Parsing the stream-json output

Read stdout line by line, `json.loads` each, pull text from `message.content[]`, `delta.text`,
or top-level `text`; ignore `type == "result"` events for streaming but keep the final
`result.result` string as a **fallback** if no incremental text was yielded.

### Don't leave zombies

`claude`/`codex` can hang after stdout closes or when the caller breaks mid-stream. Always
terminate in a `finally`: SIGTERM → wait `CLAUDE_KILL_GRACE_SECONDS` (5s) → SIGKILL. Read
stderr on a daemon thread and keep the last ~4KB for error messages.

### Wiring identifiers
`api_mode = "cli_subprocess"`, `base_url = "cli://claude-code-cli"`,
`register_transport("cli_subprocess", CliSubprocessTransport)`. The client exposes an
OpenAI-compatible `chat.completions.create(...)` facade so hermes treats it like any provider.
Both `claude` (`~/.local/bin/claude`) and `codex` (`/opt/homebrew/bin/codex`) must be on PATH.

---

## 2. CommonMark → Slack mrkdwn (so replies don't render raw)

Agents emit standard Markdown. Slack's `text` field is **mrkdwn**, NOT CommonMark. Untranslated,
`**bold**` and `[label](url)` show literally. Convert at **deliver time** on `result.text`.
Source: `~/chakra/chakra/gateway/plugins/slack.py :: to_slack_mrkdwn`.

The conversions:

| CommonMark | Slack mrkdwn |
|---|---|
| `**bold**` / `__bold__` | `*bold*` |
| `[label](url)` | `<url\|label>` |
| `# heading` … `###### h` | `*heading*` (Slack has no headings) |
| `- item` / `* item` / `+ item` | `• item` |

**Critical: be fence- and code-span-safe.** Never rewrite inside ``` fences ``` or `inline code`
— a `**` inside a code sample must stay literal. The proven approach: walk lines, toggle a
`in_fence` flag on ```` ``` ````; for non-fence lines, split on backtick runs and only convert
the non-code segments.

```python
_MD_HEADING_RE       = re.compile(r"(?m)^#{1,6}[ \t]+(.+?)[ \t]*$")
_MD_LIST_MARKER_RE   = re.compile(r"(?m)^([ \t]*)[-*+][ \t]+")
_MD_LINK_RE          = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\s]+)\)")   # (?<!!) skips images
_MD_BOLD_ASTERISK_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_MD_BOLD_UNDERSCORE_RE= re.compile(r"__(?=\S)(.+?)(?<=\S)__")

def _convert_md_segment(text):
    text = _MD_HEADING_RE.sub(r"*\1*", text)
    text = _MD_LIST_MARKER_RE.sub(r"\1• ", text)
    text = _MD_LINK_RE.sub(r"<\2|\1>", text)
    text = _MD_BOLD_ASTERISK_RE.sub(r"*\1*", text)
    return _MD_BOLD_UNDERSCORE_RE.sub(r"*\1*", text)
```

Apply it in `deliver()`: `body = {"channel": ..., "text": to_slack_mrkdwn(result.text)}`.
In Option D this becomes an **outbound hermes hook** (transform the reply text before send),
not a fork of the channel.

> instasarva's twin lives at `~/chakras/instasarva/src/instasarva/slack/blocks.py :: _to_slack_mrkdwn`
> (Block Kit `section`→`mrkdwn`). Same rules, Block-Kit shape. Pinned by `tests/test_blocks_mrkdwn.py`.

---

## 3. Slack progress reactions + operator-approval gating

### Progress reactions (every turn)
Give the user instant feedback while the (multi-minute) agent runs:

- **on receive** → add 👀 `eyes`
- **on success** → remove `eyes`, add ✅ `white_check_mark`
- **on error**   → remove `eyes`, add ❌ `x`

```python
def _react(channel, ts, emoji, *, add=True):
    if not channel or not ts:
        return
    try:
        (client.web_client.reactions_add if add else client.web_client.reactions_remove)(
            channel=channel, timestamp=ts, name=emoji)
    except Exception:
        pass    # reactions are best-effort; never let them break message handling
```

Requires the bot scope **`reactions:write`**. Source: `~/chakra/chakra/slack_cli.py`.

### Operator-approval gating (for irreversible actions)
For actions needing a human yes/no (e.g. a paper trade), post the proposal and pre-seed `+1`/`-1`,
then a socket-mode listener routes `reaction_added`:

- `+1` / `thumbsup` / `thumbs_up` → **approve**
- `-1` / `thumbsdown` / `thumbs_down` → **reject** (e.g. cancel the pending order)

Gate on an **allow-list** of Slack user IDs (`SLACK_ALLOWED_USERS`) — ignore reactions from anyone
else — and verify the reaction is on the tracked message (`(channel_id, message_ts)` in cache)
before acting. Source: `slack.py :: handle_alert_reaction`.

---

## Cross-cutting Slack rules

- **Dedup Slack retries.** Slack redelivers any event whose 3s ack window you missed. Keep a
  bounded ring of the last ~1000 `(team_id, event_id)` tuples; short-circuit duplicates. Always
  ack the socket envelope immediately (`{"envelope_id": ...}`) so Slack stops retrying.
- **Read env at request time, never at import.** `_slack_bot_token()` reads `SLACK_BOT_TOKEN`
  from `os.environ` on each call → the daemon rotates secrets (Infisical) without a restart.
- **Tokens:** app-level `xapp-` for the Socket Mode connection, bot `xoxb-` for Web API. Keep
  them root-namespaced in Infisical (`SLACK_<AGENT>_APP_TOKEN` / `_BOT_TOKEN`), injected via `iex`.
- **Scopes needed:** `reactions:write`, `chat:write`, `app_mentions:read` / `im:history` /
  `message.im` for DMs, plus `connections:write` for Socket Mode.

## Verify a working wiring
1. DM the bot → 👀 appears within ~1s (reactions + receive path OK).
2. Reply arrives formatted (no raw `**` / `[](...)`) → mrkdwn converter OK.
3. 👀 → ✅ on completion → success path OK.
4. `ps`/logs show a `claude -p …` or `codex exec …` subprocess, and NO `ANTHROPIC_API_KEY` in its
   env → subscription auth OK (not metered API).
