---
name: robinhood-portfolio-report
description: >-
  Generate a full multi-tab HTML portfolio + trading-activity report from the
  Robinhood trading MCP. Produces an Overview (account value, allocation donut,
  holdings, open P&L), Holdings·2Y (per-ticker price + MA50/MA200 + RSI + MACD
  charts from Yahoo Finance, plus PluseFinance fundamentals if available),
  Activity (realized P&L reconstructed from order fills, win/loss, monthly
  volume, per-symbol table), and a Trades tab (filterable/sortable per-fill
  drill-down). Use when the user asks for a portfolio report, dashboard, "full
  analysis like TradingView", account performance, realized/unrealized P&L,
  trade history, or "how's my Robinhood account doing". Requires the
  robinhood-trading MCP to be connected.
tier: tools
tags: [robinhood, trading, portfolio, mcp, finance, report, html, dashboard, pnl]
version: 1
---

# robinhood-portfolio-report

Builds a single self-contained HTML report from the **robinhood-trading MCP**.
Honest by design: it labels exactly what the MCP can and cannot provide.

## What the MCP CAN and CANNOT give you (read first — these are the gotchas)

- ✅ Current account/portfolio snapshot, positions, live quotes, full order
  history. ❌ **No portfolio-value-over-time endpoint.** There is no way to get
  the broker's official account-value line from this MCP. Do **not** fabricate
  one. The honest equity curve must be reconstructed from fills, and even that
  is unreliable in absolute terms (see below) — for the true line, tell the user
  to open the Robinhood app → Account → tap the graph → 1Y.
- ⚠️ **Order history floors at the earliest available fill**, often only ~6–8
  months — not necessarily a full year. State the actual window.
- ⚠️ Some fills come back with a **blank `symbol`** (broker quirk) → marked
  `unmapped`, excluded from realized P&L.
- ⚠️ Positions opened **before** the history window show orphan quantities →
  marked `prewindow`, excluded from realized P&L.
- ⚠️ This is often a **margin** account: gross traded notional can hugely exceed
  deposited capital (round-trip day-trading). Say "gross volume", never "deposits".
- 🔒 **Mask account numbers** to the user (`••••6064`), but pass the full value to
  MCP tools unchanged.
- 💵 Realized P&L is only trustworthy for **closed round-trips** (symbol opened
  AND closed inside the window, net qty ≈ 0). The script computes it only for those.

PluseFinance MCP (fundamentals/news/prediction) is **optional** — it is a
separate, credit-metered server. If it's connected and has credit, enrich the
Holdings tab with fundamentals; if not, the report renders fine without them.

## Step 1 — collect data from the MCP

Call these robinhood-trading MCP tools:

1. `get_accounts` → pick the account(s). Default account is `is_default:true`.
   If multiple have holdings, ask the user which, or report each.
2. For the chosen `account_number`:
   - `get_portfolio` → `cash`, `total_value`, `buying_power`.
   - `get_equity_positions` → each `symbol`, `quantity`, `average_buy_price`.
   - `get_equity_quotes` (held symbols) → `last_trade_price` (the live price).
   - `get_equity_orders` with `state:"filled"` and `created_at_gte` ~13 months
     back. **This response is large and is usually written to a tool-results
     `.txt` file** — that file is plain JSON; pass its path to the script.

If `get_equity_orders` returns an "exceeds maximum allowed tokens" error, it
still saved the full JSON to a file — grab that path from the error message.

## Step 2 — write inputs.json

Create `inputs.json` (numbers from Step 1; use `last_trade_price` for `quotes`):

```json
{
  "account_mask": "••••6064",
  "as_of": "2026-05-29",
  "cash": 142.96,
  "holdings": { "GDC": {"qty": 17000.0, "avg": 0.1345},
                "RGTI": {"qty": 0.066176, "avg": 32.1797} },
  "quotes":   { "GDC": 0.1139, "RGTI": 25.54 },
  "fundamentals": {}
}
```

`fundamentals` is optional. If PluseFinance `get_ticker_data` worked, add per
symbol: `{name,sector,mcap,beta,range,short,fpe,pb,roe,opm,cr,de,emp,target,
upside,rec:{sb,b,h,s,ss}|null,note}`. Leave `{}` to skip.

## Step 3 — run the generator

One-time venv (reuse if it exists):

```bash
SKILL_DIR=~/.skills-hub/tools/robinhood-portfolio-report
python3 -m venv ~/.cache/rh-report-venv 2>/dev/null
~/.cache/rh-report-venv/bin/pip install -q -r "$SKILL_DIR/requirements.txt"
```

Generate (point `--orders` at the saved order-history JSON/.txt):

```bash
~/.cache/rh-report-venv/bin/python "$SKILL_DIR/gen_report.py" \
  --inputs /path/to/inputs.json \
  --orders /path/to/get_equity_orders-result.txt \
  --out ~/portfolio-full-report.html
open ~/portfolio-full-report.html
```

The script prints a summary line (`realized=… wins=… loss=… gross=… acct=…`).
It fetches 2Y daily history from Yahoo Finance for each held symbol and computes
MA50/MA200, RSI-14, MACD, annualized vol, and max drawdown locally.

## Step 4 — report to the user

Quote the snapshot, the realized P&L + win rate, and the **data-coverage caveats**
(history window, account-value-curve limitation, any unmapped/prewindow symbols,
whether PluseFinance enrichment was available). Never present the reconstruction
as the broker's official numbers.

## Files in this skill

- `gen_report.py` — data pipeline + report generator (argparse CLI).
- `template.html` — the HTML/JS template (`__DATA__` placeholder injected by the script).
- `requirements.txt` — yfinance, pandas, numpy.

## Safety

Read-only reporting. This skill never places, modifies, or cancels orders.
Always append **"Not financial advice."** and never auto-trade off the report.
