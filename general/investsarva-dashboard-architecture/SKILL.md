---
name: investsarva-dashboard-architecture
description: >
  Architecture reference for the InvestSarva trading dashboard at ~/investsarva-dashboard.
  Use when working on any feature, bug, or modification in the dashboard. Provides the data flow,
  service layer, widget structure, and key conventions. Triggers: any work on the InvestSarva
  dashboard, "how does the dashboard work", "where is X in the dashboard", "dashboard architecture",
  or when needing to understand the relationship between dataStore, scanners, WebSocket, and widgets.
---

# InvestSarva Dashboard Architecture

React 19 + TypeScript + Vite 7 + FlexLayout-React trading dashboard.

## Data Flow

```
Alpaca REST API ──► dataStore (singleton) ──► scanner builders ──► Scanner.tsx
                         ▲                         ▲
Alpaca SIP WebSocket ────┘    Alert Trackers ──────┘
  (trades/quotes)           (momentum/hod/pillar)
```

## Service Layer

| Service | File | Role |
|---------|------|------|
| **api.ts** | `src/services/api.ts` | REST calls: movers, snapshots, news, profiles, SI |
| **dataStore.ts** | `src/services/dataStore.ts` | Shared singleton store, auto-refresh, session mgmt |
| **alpacaWS.ts** | `src/services/alpacaWS.ts` | WebSocket: SIP trades/quotes/bars streaming |
| **scanner.ts** | `src/services/scanner.ts` | Scanner builders, BUILDERS map, ScannerRow type |
| **momentumTracker.ts** | `src/services/momentumTracker.ts` | Running Up/Down alert feed |
| **hodTracker.ts** | `src/services/hodTracker.ts` | HOD Momentum alert feed |
| **pillarTracker.ts** | `src/services/pillarTracker.ts` | 5 Pillars alert feed |
| **preMarketTracker.ts** | `src/services/preMarketTracker.ts` | Pre-market mover discovery |

## dataStore Singleton

Central hub. All data lives here. Key exports:

- `ensureData()` — fetch/refresh all data (REST)
- `getSnap(symbol)` — snapshot (dailyBar, prevDailyBar, latestTrade)
- `getProfile(symbol)` — company profile (float, industry)
- `getNews(symbol)` — latest news headline/url
- `getShortInterest(symbol)` — SI data
- `getSession()` — "pre" | "regular" | "post" | "closed"
- `subscribeStore(cb)` — subscribe to data changes
- `startAutoRefresh()` / `stopAutoRefresh()` — lifecycle

**Refresh cycle**: REST every 8s (movers + snapshots), WS continuous (trades).

## Scanner Architecture

Two models (see `scanner-config` and `alert-tracker-pattern` skills):

- **Snapshot**: `buildGainers(d)`, etc. — one row per symbol, rebuilt on each refresh
- **Feed**: `hodTracker.getAlerts()`, etc. — append-only alert log via WebSocket

All builders registered in `scanner.ts` BUILDERS map. Scanner.tsx calls `fetchScannerData(scannerType)`.

## Widget Layer

| Widget | File | Purpose |
|--------|------|---------|
| Scanner | `src/widgets/Scanner.tsx` | Scanner table with colored cells, sort, fire icons |
| StockQuote | `src/widgets/StockQuote.tsx` | Individual stock quote display |

## Key Conventions

- **ZERO hardcoded data** — every value from real APIs
- **ZERO per-scanner API calls** — all data from shared dataStore
- **Alpaca SIP feed** — `feed=sip` on all REST, `wss://stream.data.alpaca.markets/v2/sip` for WS
- **All sessions active** — pre-market, regular, after-hours. No session gating on trackers
- **Fire icon = NEWS** — not high % change. Red=critical, Orange=important, Yellow=notable
- **Vite proxy**: `/finnhub` → finnhub.io, `/gnw` → localhost:3000

## API Keys

- Alpaca: in `.env` and `api.ts` (PKTJBTMHNM4SD3NSXL3XIB7KFG)
- Finnhub: `VITE_FINNHUB_API_KEY` in `.env`

## Column/Scanner Config

See `scanner-config` skill for details on `src/data/scannerTypes.ts`.

## Alert Tracker Pattern

See `alert-tracker-pattern` skill for creating new WebSocket-driven trackers.
