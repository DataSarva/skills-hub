#!/usr/bin/env python3
"""
robinhood-portfolio-report — combined HTML report generator.

Consumes data the agent collected from the Robinhood MCP (+ optional
PluseFinance fundamentals), pulls 2Y price history from Yahoo Finance,
reconstructs realized P&L from order fills, and emits a single self-contained
multi-tab HTML report (Overview / Holdings 2Y / Activity / Trades).

Usage:
    python gen_report.py --inputs inputs.json --orders orders.json --out report.html

inputs.json schema:
{
  "account_mask": "....6064",
  "as_of": "2026-05-29",
  "cash": 142.96,
  "holdings": { "GDC": {"qty": 17000.0, "avg": 0.1345},
                "RGTI": {"qty": 0.066176, "avg": 32.1797} },
  "quotes":   { "GDC": 0.1139, "RGTI": 25.54 },           # live last price
  "fundamentals": {                                        # OPTIONAL (PluseFinance)
     "GDC": {"name":"GD Culture Group","sector":"...","mcap":"$6.68M","beta":2.09,
             "range":"$0.09-$9.91","short":"13.72%","fpe":"N/A","pb":"0.01",
             "roe":"-138.9%","opm":"N/A","cr":"0.11","de":"0.23","emp":5,
             "target":"N/A","upside":"N/A","rec":null,"note":"..."}
  }
}

orders.json: the RAW Robinhood MCP get_equity_orders result, i.e. the object
with data.orders[] (filled state). If the MCP saved it to a tool-results .txt
file because it was too large, just point --orders at that file — it's JSON.
"""
import argparse, json, math, sys
from collections import defaultdict


def load_orders(path):
    raw = json.load(open(path))
    if isinstance(raw, dict) and "data" in raw and "orders" in raw["data"]:
        return raw["data"]["orders"]
    if isinstance(raw, dict) and "orders" in raw:
        return raw["orders"]
    if isinstance(raw, list):
        return raw
    raise SystemExit("orders.json: cannot find orders[] (expected data.orders)")


def build_trades(orders):
    trades = []
    for o in orders:
        if o.get("state") != "filled":
            continue
        qty = float(o.get("cumulative_quantity") or o.get("quantity") or 0)
        price = float(o.get("average_price") or o.get("price") or 0)
        fee = float(o.get("fees") or 0)
        trades.append({
            "date": (o.get("last_transaction_at") or o.get("created_at") or "")[:10],
            "sym": o.get("symbol") or "(unmapped)",
            "side": o.get("side", ""),
            "qty": round(qty, 4), "price": round(price, 4),
            "notional": round(qty * price, 2), "fee": round(fee, 2),
            "type": o.get("type", "market"), "agent": o.get("placed_agent", "user"),
        })
    trades.sort(key=lambda t: t["date"])
    return trades


def aggregate(trades):
    agg = defaultdict(lambda: {"buyq": 0.0, "sellq": 0.0, "buy": 0.0, "sell": 0.0, "n": 0, "last": "0000"})
    for t in trades:
        a = agg[t["sym"]]; a["n"] += 1; a["last"] = max(a["last"], t["date"])
        if t["side"] == "buy":
            a["buyq"] += t["qty"]; a["buy"] += t["notional"] + t["fee"]
        else:
            a["sellq"] += t["qty"]; a["sell"] += t["notional"] - t["fee"]
    rows, realized, wins, loss, bars = [], 0.0, 0, 0, []
    for s, a in agg.items():
        netq = a["buyq"] - a["sellq"]; traded = max(a["buyq"], a["sellq"], 1)
        pl = a["sell"] - a["buy"]
        if s == "(unmapped)":
            st = "unmapped"
        elif abs(netq) < max(1.0, 0.01 * traded) and a["buyq"] > 0 and a["sellq"] > 0:
            st = "closed"
        elif a["buyq"] > 0 and a["sellq"] == 0:
            st = "open"
        elif a["sellq"] > 0 and a["buyq"] == 0:
            st = "prewindow"
        else:
            st = "partial"
        if st == "closed":
            realized += pl; bars.append({"sym": s, "pl": round(pl, 2)})
            wins += pl >= 0; loss += pl < 0
        rows.append({"sym": s, "n": a["n"], "buy": round(a["buy"], 2), "sell": round(a["sell"], 2),
                     "pl": round(pl, 2), "status": st, "last": a["last"], "netq": round(netq, 4)})
    rows.sort(key=lambda r: (r["status"] != "closed", -abs(r["pl"])))
    bars.sort(key=lambda b: b["pl"])
    return rows, round(realized, 2), wins, loss, bars


def monthly(trades, agg_rows):
    mon = defaultdict(lambda: [0.0, 0.0, 0])
    for t in trades:
        m = t["date"][:7]
        if t["side"] == "buy":
            mon[m][0] += t["notional"]
        else:
            mon[m][1] += t["notional"]
        mon[m][2] += 1
    return [{"m": m, "buy": round(mon[m][0], 2), "sell": round(mon[m][1], 2), "n": mon[m][2]} for m in sorted(mon)]


def rsi(s, n=14):
    import pandas as pd
    d = s.diff(); up = d.clip(lower=0).rolling(n).mean(); dn = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, float("nan")))


def price_history(symbols, quotes):
    import yfinance as yf, pandas as pd, numpy as np
    out = {}
    for t in symbols:
        try:
            df = yf.download(t, period="2y", interval="1d", auto_adjust=True, progress=False)
        except Exception as e:
            print(f"  ! {t}: download failed ({e})", file=sys.stderr); continue
        if df.empty:
            print(f"  ! {t}: no price data", file=sys.stderr); continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(); close = df["Close"]
        df["MA50"] = close.rolling(50).mean(); df["MA200"] = close.rolling(200).mean()
        df["RSI"] = rsi(close)
        ef, es = close.ewm(span=12).mean(), close.ewm(span=26).mean()
        macd = ef - es; sig = macd.ewm(span=9).mean(); hist = macd - sig
        ret = close.pct_change().dropna()
        cur = float(quotes.get(t, close.iloc[-1]))
        ya = close.iloc[-252] if len(close) >= 252 else close.iloc[0]
        ytd = close[close.index >= f"{close.index[-1].year}-01-01"]
        roll = close.cummax()

        def arr(x):
            return [None if (v is None or (isinstance(v, float) and math.isnan(v))) else round(float(v), 6) for v in x]

        def now(x):
            v = x.iloc[-1]; return None if math.isnan(v) else float(v)

        out[t] = {"dates": [d.strftime("%Y-%m-%d") for d in df.index],
                  "close": arr(close), "ma50": arr(df["MA50"]), "ma200": arr(df["MA200"]),
                  "rsi": arr(df["RSI"]), "macd": arr(macd), "signal": arr(sig), "hist": arr(hist),
                  "cur": cur, "hi": float(close.max()), "lo": float(close.min()),
                  "perf_1y": (cur / float(ya) - 1) * 100,
                  "perf_ytd": (cur / float(ytd.iloc[0]) - 1) * 100 if len(ytd) > 1 else 0.0,
                  "vol_ann": float(ret.std() * math.sqrt(252) * 100),
                  "mdd": float((close / roll - 1).min() * 100),
                  "rsi_now": now(df["RSI"]), "ma50_now": now(df["MA50"]), "ma200_now": now(df["MA200"])}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--orders", required=True)
    ap.add_argument("--out", default="portfolio-full-report.html")
    a = ap.parse_args()

    I = json.load(open(a.inputs))
    holdings = I.get("holdings", {}); quotes = I.get("quotes", {}); cash = float(I.get("cash", 0))
    trades = build_trades(load_orders(a.orders))
    if not trades:
        raise SystemExit("no filled trades found in orders.json")
    rows, realized, wins, loss, bars = aggregate(trades)
    months = monthly(trades, rows)
    gross = round(sum(r["buy"] + r["sell"] for r in rows), 2)

    print(f"pulling 2Y price history for {list(holdings)} ...", file=sys.stderr)
    px = price_history(list(holdings.keys()), quotes)

    tot_val = sum(holdings[s]["qty"] * quotes.get(s, 0) for s in holdings)
    tot_cost = sum(holdings[s]["qty"] * holdings[s]["avg"] for s in holdings)
    snap = {"acct": round(tot_val + cash, 2), "equity": round(tot_val, 2), "cost": round(tot_cost, 2),
            "cash": cash, "pl": round(tot_val - tot_cost, 2),
            "plp": round((tot_val / tot_cost - 1) * 100, 2) if tot_cost else 0.0,
            "rows": [{"sym": s, "qty": holdings[s]["qty"], "avg": holdings[s]["avg"],
                      "last": quotes.get(s, 0), "val": round(holdings[s]["qty"] * quotes.get(s, 0), 2),
                      "pl": round(holdings[s]["qty"] * (quotes.get(s, 0) - holdings[s]["avg"]), 2),
                      "plp": round((quotes.get(s, 0) / holdings[s]["avg"] - 1) * 100, 2) if holdings[s]["avg"] else 0.0}
                     for s in holdings]}
    # allocation
    alloc = [{"sym": s, "v": snap_row["val"]} for s, snap_row in zip(holdings, snap["rows"])]
    alloc.append({"sym": "Cash", "v": cash})

    blob = {"meta": {"mask": I.get("account_mask", ""), "as_of": I.get("as_of", "")},
            "snap": snap, "alloc": alloc, "fund": I.get("fundamentals", {}), "px": px,
            "act": {"realized": realized, "wins": wins, "loss": loss, "closed_n": wins + loss,
                    "gross": gross, "months": months, "closed_bars": bars, "symrows": rows,
                    "window": {"start": trades[0]["date"], "end": I.get("as_of", trades[-1]["date"]),
                               "fills": len(trades), "symbols": len(rows)}},
            "trades": trades}

    html = TEMPLATE.replace("__DATA__", json.dumps(blob))
    open(a.out, "w").write(html)
    print(f"wrote {a.out} ({len(html):,} bytes)", file=sys.stderr)
    print(f"realized=${realized:,.2f}  wins={wins} loss={loss}  gross=${gross:,.0f}  "
          f"acct=${snap['acct']:,.2f}", file=sys.stderr)


# ---- HTML template lives in template.html next to this script ----
import os
TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")).read()

if __name__ == "__main__":
    main()
