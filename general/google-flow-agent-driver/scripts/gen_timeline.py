#!/usr/bin/env python3
"""shots.json -> remotion/timeline.json (frame-accurate timeline for the Remotion comp).

Each shot becomes a sequence: clip (cover-fit), its Telugu VO (starts at shot start),
synced Telugu subtitle (shown for the VO duration), optional emphasis kicker.
Run from the v3/ dir.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Edition-aware: SHOTS = which shots file (master shots.json, or shots.yt60.json, etc.);
# TIMELINE = output path. clip/audio path strings stay "clips/.."/"audio/.." and are resolved
# by the remotion/public symlinks the edition wrapper repoints. Defaults = master (Instagram).
SHOTS = os.environ.get("SHOTS", os.path.join(ROOT, "shots.json"))
TIMELINE = os.environ.get("TIMELINE", os.path.join(ROOT, "remotion", "timeline.json"))
d = json.load(open(SHOTS))
fps = d["meta"]["fps"]

shots, cur = [], 0
for s in d["shots"]:
    df = int(round(s["dur"] * fps))
    vf = int(round(s.get("vo_dur", s["dur"]) * fps))
    shots.append({
        "id": s["id"],
        "clip": f"clips/shot{s['id']}.mp4",
        "audio": f"audio/shot{s['id']}.mp3",
        "startFrame": cur,
        "durFrames": df,
        "voFrames": vf,
        "narration": s["narration_te"],
        "onscreen": s.get("onscreen_te", ""),
    })
    cur += df

out = {
    "fps": fps, "width": d["meta"]["width"], "height": d["meta"]["height"],
    "totalFrames": cur, "music": "music/bed.wav", "title": d["meta"]["title_te"],
    "shots": shots,
}
os.makedirs(os.path.dirname(TIMELINE), exist_ok=True)
json.dump(out, open(TIMELINE, "w"), ensure_ascii=False, indent=2)
print(f"wrote {TIMELINE}  totalFrames={cur} ({cur/fps:.1f}s) shots={len(shots)}")
