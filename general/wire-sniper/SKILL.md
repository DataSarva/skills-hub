---
name: wire-sniper
description: Wire Sniper real-time news catalyst alert system for the InvestSarva dashboard. Use when working on Wire Sniper features — the WebSocket client, alert widget, audio alerts, types, or Python backend integration. Triggers on mentions of "wire sniper", "news alerts", "catalyst alerts", "wire-sniper.py", "wireSniperWS", or tasks involving the Wire Sniper panel in the trading dashboard.
---

# Wire Sniper Dashboard Integration

Wire Sniper catches news catalysts (BusinessWire, PRNewswire, GlobeNewsWire) in <3 seconds, scores them semantically, cross-references stock DNA (price, float, mcap, short interest), and pushes alerts via WebSocket.

## Architecture

See [references/architecture.md](references/architecture.md) for full data flow, file map, and key patterns.

## Key Files

| File | Purpose |
|------|---------|
| `src/data/wireSniperTypes.ts` | TypeScript interfaces (`WireSniperAlert`, `CatalystData`, `DNAData`, `TradeData`) + helper functions |
| `src/services/wireSniperWS.ts` | Singleton WebSocket client — connects to `ws://localhost:8765`, auto-reconnect, Web Audio API alerts |
| `src/widgets/WireSniper.tsx` | Alert panel widget — color-coded rows, filters, auto-switch, expandable details |
| `src/index.css` | CSS keyframes: `wireSniperCriticalPulse`, `wireSniperFlashIn`, `wireSniperConnected` |
| `src/App.tsx` | Factory case `'wiresniper'` + layout row (weight 8, top of screen) |
| `src/components/Sidebar.tsx` | Tool entry with `Crosshair` icon (first in tools list) |

## Critical Rules

1. **Always use `import type` for interfaces** — Vite/esbuild strips type-only exports. Value imports of interfaces cause blank white page.
   ```ts
   // CORRECT
   import { parseAlertLevel } from '../data/wireSniperTypes';
   import type { WireSniperAlert, AlertLevel } from '../data/wireSniperTypes';

   // WRONG — causes runtime error
   import { WireSniperAlert, parseAlertLevel } from '../data/wireSniperTypes';
   ```

2. **Audio plays BEFORE React state updates** — in `wireSniperWS.ts`, `playAlertSound()` fires before handler notifications for fastest user response.

3. **No debouncing** — every WebSocket message triggers immediate state update. HFT — milliseconds matter.

4. **Always-on, 24/7** — no time window restrictions. News drops at any hour (pre-market, after-hours, overnight).

5. **Zero coupling to other services** — `wireSniperWS.ts` is fully independent from `alpacaWS.ts` and `dataStore.ts`. If Wire Sniper backend is down, rest of dashboard works normally.

## Common Tasks

**Add a new alert level**: Update `AlertLevel` type in `wireSniperTypes.ts`, add color/bg cases, update filter toggles in `WireSniper.tsx`.

**Change audio**: Modify `playAlertSound()` in `wireSniperWS.ts`. Frequencies and timing in `playBeep()` calls. Uses Web Audio API oscillators — no external files.

**Modify layout position**: Change the Wire Sniper row in `defaultLayout` in `App.tsx`. Weight 8 = ~7% of screen height.

**Add new fields to alerts**: Add to `WireSniperAlert` interface in `wireSniperTypes.ts`, display in the expandable detail panel in `WireSniper.tsx`.

## Wire Sniper Backend

- **Script**: `wire-sniper.py` (Python)
- **WebSocket**: `ws://localhost:8765` (no auth)
- **JSON format**: `{ event, level, ticker, title, source, url, catalyst, dna, combined_score, trade, timestamp, latency_ms }`
- **Alert levels**: CRITICAL (combined_score >= 100), HIGH (>= 60), WATCH (< 60)
