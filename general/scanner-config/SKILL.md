---
name: scanner-config
description: >
  Add, modify, or configure scanner types and columns in the InvestSarva trading dashboard.
  Use when adding a new scanner, changing scanner columns, modifying scanner filters, updating
  sort behavior, or wiring a scanner to a different data source. Triggers: "add scanner",
  "new scanner type", "change scanner columns", "fix scanner layout", "add column to scanner",
  "scanner not showing right data", or any scanner configuration task in ~/investsarva-dashboard.
---

# Scanner Configuration

Configure scanner types, column layouts, and data builders for the InvestSarva dashboard.

## Key Files

| File | Purpose |
|------|---------|
| `src/data/scannerTypes.ts` | Column configs, scanner type definitions, ID/name mapping |
| `src/services/scanner.ts` | Builder functions, BUILDERS map, ScannerRow type, alertToRow converters |
| `src/widgets/Scanner.tsx` | UI rendering, cell coloring, sort, header |

## Adding a New Scanner

### 1. Define columns in scannerTypes.ts

Use existing column presets or create new ones:

```typescript
// Existing presets
COL_TIME, COL_SYMBOL, COL_PRICE, COL_VOLUME, COL_FLOAT,
COL_REL_VOL_DAILY, COL_REL_VOL_5M, COL_GAP, COL_CHANGE_CLOSE,
COL_SHORT_INT, COL_STRATEGY, COL_POS_RANGE, COL_CHANGE_OPEN

// Custom column
const COL_CUSTOM: ColumnConfig = {
  key: "customField",      // must match ScannerRow field
  label: "Display Label",
  width: 100,
  align: "right",
  colorCode: "change"      // "change"|"gap"|"volume"|"float"|"strategy"|"none"
};
```

### 2. Create column array and register scanner type

```typescript
const MY_SCANNER_COLS: ColumnConfig[] = [
  COL_TIME, COL_SYMBOL, COL_PRICE, COL_VOLUME, COL_FLOAT,
  COL_REL_VOL_DAILY, COL_CHANGE_CLOSE, COL_STRATEGY,
];

// Add to SCANNER_TYPES array:
{ id: "my-scanner", name: "My Scanner", category: "strategy", columns: MY_SCANNER_COLS,
  defaultSortKey: "time", defaultSortDir: "desc" },
```

### 3. Add builder in scanner.ts BUILDERS map

**For snapshot scanners** (one row per symbol):
```typescript
"My Scanner": (d) => buildGainers(d).filter(r => r.price < 20 && r.changeFromClose > 5),
```

**For feed scanners** (alert tracker — see alert-tracker-pattern skill):
```typescript
"My Scanner": (_d) => myTracker.getAlerts(200).map(a => myAlertToRow(a, getSnap(a.symbol))),
```

### 4. Add ScannerRow field if needed

In scanner.ts, add to the `ScannerRow` interface:
```typescript
customField?: number;
```

Populate it in `buildRow()` or your alertToRow converter.

## Column Color Codes

| colorCode | Cell Background | When |
|-----------|----------------|------|
| `"change"` | Green (positive) / Red (negative) | % change values |
| `"gap"` | Green (positive) / Red (negative) | Gap % values |
| `"volume"` | Blue gradient by size | Volume columns |
| `"float"` | Green gradient (brighter = smaller) | Float columns |
| `"strategy"` | Category-based distinct colors | Strategy/alert name |
| `"none"` | Transparent | No coloring |

Auto-colored by key (no colorCode needed): `relVolDaily`, `relVol5m` (teal), `posInRange` (red-green), `rsi1Min` (red-green), `bouncePercent` (green).

## Scanner Categories

- `"strategy"` — Alert-type scanners (time-sorted, often feed-based)
- `"scanner"` — List-type scanners (metric-sorted, snapshot-based)

## Common Column Layouts (from target)

**HOD Momentum**: Time, Symbol, Price, Volume, Float, RelVol(Daily), RelVol(5min), Gap, ChangeClose, SI, Strategy

**5 Pillars Alert**: Time, Symbol, Price, Volume, Float, RelVol(5min), RelVol(Daily), Gap, ChangeClose, SI, Strategy

**5 Pillars Scan**: RelVol(Daily), Symbol, Price, Volume, Float, RelVol(5min), Gap, ChangeClose, SI, PosInRange

**Top Gappers**: Gap, Symbol, Price, Volume, Float, RelVol(Daily), RelVol(5min), ChangeClose, SI

## Available Builder Helpers

- `buildGainers(d)` — Top gainers by % change
- `buildLosers(d)` — Top losers
- `buildActives(d)` — Most active by volume
- `buildHoD(d)` — High of day (snapshot, legacy)
- `buildGappers(d)` — Stocks with gap >= 3%
- `buildContinuation(d)` — Gap + continuation in same direction
- `buildReversal(d)` — Gap then reversal
- `dedup(...lists)` — Merge mover lists, remove duplicates
