#!/usr/bin/env python3
"""shots(v2).json -> remotion/timeline.json with per-beat segment lists (multi-clip beats).
Env: SHOTS, TIMELINE, SHOW_KEYWORDS(=1)."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.environ.get("SHOTS", os.path.join(ROOT, "shots_v2.json"))
TIMELINE = os.environ.get("TIMELINE", os.path.join(ROOT, "remotion", "timeline.json"))
show_kw = os.environ.get("SHOW_KEYWORDS", "1") != "0"
d = json.load(open(SHOTS))
fps = d["meta"]["fps"]

shots, cur = [], 0
for s in d["shots"]:
    segs = []
    for seg in s["segments"]:
        segs.append({"clip": f"clips/{seg['clip']}.mp4", "durFrames": int(round(seg["dur"] * fps))})
    df = sum(x["durFrames"] for x in segs)
    vf = int(round(s.get("vo_dur", s["dur"]) * fps))
    shots.append({
        "id": s["id"],
        "audio": f"audio/shot{s['id']}.mp3",
        "startFrame": cur,
        "durFrames": df,
        "voFrames": vf,
        "segments": segs,
        "narration": s.get("narration_te", ""),
        "onscreen": s.get("onscreen_te", ""),
        "keyword": s.get("keyword_te", "") if show_kw else "",
        "endcard": s.get("endcard_te", ""),
    })
    cur += df

out = {"fps": fps, "width": d["meta"]["width"], "height": d["meta"]["height"],
       "totalFrames": cur, "music": "music/bed.wav", "title": d["meta"]["title_te"], "shots": shots}
os.makedirs(os.path.dirname(TIMELINE), exist_ok=True)
json.dump(out, open(TIMELINE, "w"), ensure_ascii=False, indent=2)
print(f"wrote {TIMELINE}  totalFrames={cur} ({cur/fps:.1f}s) shots={len(shots)}")
