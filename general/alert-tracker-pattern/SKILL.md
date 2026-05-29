---
name: alert-tracker-pattern
description: >
  Create real-time WebSocket-driven alert tracker services for the InvestSarva trading dashboard.
  Use when adding a new scanner alert type (like Running Up, HOD Momentum, 5 Pillars), converting
  a snapshot-based scanner to a feed-based scanner, or modifying alert trigger criteria. Triggers:
  "add new alert tracker", "create scanner feed", "new momentum scanner", "convert scanner to
  real-time feed", "add alert type", or any request to build a WebSocket-driven alert accumulator
  in the InvestSarva dashboard at ~/investsarva-dashboard.
---

# Alert Tracker Pattern

Create real-time alert feed trackers for the InvestSarva dashboard. These are WebSocket-driven
singletons that hook into Alpaca SIP trade stream and fire timestamped alerts when criteria match.

## Feed vs Snapshot

- **Feed (alert tracker)**: Append-only log. Same symbol appears many times. Used by: Running Up/Down, HOD Momentum, 5 Pillars Alert.
- **Snapshot**: One row per symbol, rebuilt every 5s. Used by: Top Gainers, Gappers, 5 Pillars Scan.

## Existing Trackers

| Tracker | File | Trigger |
|---------|------|---------|
| momentumTracker | `src/services/momentumTracker.ts` | >=1% price move in 90s window |
| hodTracker | `src/services/hodTracker.ts` | Price within 1.5% of daily high, <$20, change>=2% |
| pillarTracker | `src/services/pillarTracker.ts` | >=3 of 5 pillars (relVol>=5x, change>=10%, low float, momentum, catalyst) |

## 4-Step Process

### 1. Create tracker singleton

Create `src/services/<name>Tracker.ts`. Read `src/services/hodTracker.ts` as the template — it's the simplest. Every tracker needs:

- `activate(getSnapFn)` / `deactivate()` — lifecycle tied to WS
- `handleTrade(trade: TradeUpdate)` — core detection on every trade
- `fireAlert(...)` — build alert, prepend to array, prune, notify
- `getAlerts(limit)` — read alerts for scanner
- `onAlert(callback)` — subscribe for store notifications
- `syncSymbols(symbols, getSnapFn)` — update snap accessor on refresh

### 2. Wire into dataStore.ts

```typescript
import { <name>Tracker } from "./<name>Tracker";

// startAutoRefresh():
<name>Tracker.activate((sym) => store.snapshots.get(sym));
<name>Tracker.onAlert(() => notifyListeners());

// ensureData() sync block:
<name>Tracker.syncSymbols(symbolArr, (sym) => store.snapshots.get(sym));

// stopAutoRefresh():
<name>Tracker.deactivate();
```

### 3. Add alertToRow converter in scanner.ts

```typescript
import { <name>Tracker, type <Name>Alert } from "./<name>Tracker";

function <name>AlertToRow(alert: <Name>Alert, snap: SnapData | undefined): ScannerRow {
  // Enrich with: getProfile, getNews, getNewsPriority, getShortInterest
}
```

### 4. Register builder in BUILDERS map

```typescript
"Scanner Name": (_d) => <name>Tracker.getAlerts(200).map(a => <name>AlertToRow(a, getSnap(a.symbol))),
```

## Constants (match existing trackers)

| Constant | Value | Purpose |
|----------|-------|---------|
| COOLDOWN_MS | 8000 | Min gap between alerts per symbol |
| MAX_ALERTS | 500 | Cap on stored alerts |
| ALERT_TTL_MS | 1800000 | 30-minute expiry |
| ALERT_FREQ_WINDOW_MS | 5000 | "(N in Xsec)" grouping window |

## 12h Time Format (required)

```typescript
const d = new Date();
let h = d.getHours();
const ap = h >= 12 ? "pm" : "am";
h = h % 12 || 12;
const alertTimeStr = `${h.toString().padStart(2, "0")}:${m}:${s} ${ap}`;
```

## Data Access (zero API calls — all from shared store)

- `getSnap(symbol)` — dailyBar, prevDailyBar, latestTrade, minuteBar, prevClose
- `getProfile(symbol)` — shareOutstanding, finnhubIndustry, ipo
- `getNews(symbol)` — headline, url, source
- `getShortInterest(symbol)` — shortPercentOfFloat

## Rules

- NO session gating — trackers must work in pre-market, regular, and after-hours
- NO direct API calls — read only from shared dataStore
- Always use `feed=sip` WebSocket (extended hours included)
- Always deactivate in `stopAutoRefresh()`
