#!/usr/bin/env python3
"""Generate content-aware sfx_cues_<g>.json from shots_<g>.json (per-shot durations).

Each shot has a known location/event (from identification). We place one ambience bed per
location + event hits at offsets within the shot, and an anthem vocal swell over the climax.
Times are absolute on the VO render timeline (cumulative shot durations).

Usage: gen_sfx_cues.py <male|female>
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = sys.argv[1]
SHOTS_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, f"shots_{G}.json")
shots = json.load(open(SHOTS_PATH))["shots"]

# per-shot recipe: beds (long file, trimmed to shot) + hits (one-shots at offset)
# (file, off, vol, kind)  kind: 'bed' (trim=shotdur) or 'hit'
RECIPE = {
    1:  [("wind_bed.mp3", 0.0, 0.13, "bed"), ("whoosh.mp3", 0.1, 0.35, "hit")],           # aerial elevation
    2:  [("wind_bed.mp3", 0.0, 0.07, "bed")],                                               # inscription, mysterious
    3:  [("nature_amb.mp3", 0.0, 0.15, "bed"), ("fire_crackle.mp3", 0.6, 0.32, "hit"),
         ("fire_crackle.mp3", 2.4, 0.3, "hit"), ("fire_crackle.mp3", 4.2, 0.3, "hit")],     # tribe + fire dusk
    4:  [("wind_bed.mp3", 0.0, 0.08, "bed"), ("whoosh.mp3", 0.1, 0.28, "hit")],             # temples, divine
    5:  [("birds.mp3", 0.0, 0.16, "bed")],                                                   # village paddy sunrise
    6:  [("war_amb.mp3", 0.0, 0.2, "hit"), ("horses.mp3", 0.5, 0.34, "hit"),
         ("war_amb.mp3", 3.4, 0.18, "hit"), ("battle.mp3", 1.8, 0.38, "hit")],              # fort siege battle
    7:  [("wind_bed.mp3", 0.0, 0.06, "bed")],                                                # macro brush, reverent
    8:  [("wind_bed.mp3", 0.0, 0.05, "bed")],                                                # nizam palace, quiet
    9:  [("wind_bed.mp3", 0.0, 0.05, "bed"), ("whoosh.mp3", 0.1, 0.18, "hit")],             # 1956 map
    10: [("war_amb.mp3", 0.3, 0.16, "hit"), ("anthem_swell.mp3", 3.0, 0.5, "hit"),
         ("crowd_cheer.mp3", 5.0, 0.22, "hit"), ("fireworks.mp3", 5.6, 0.4, "hit"),
         ("fireworks2.mp3", 7.4, 0.4, "hit"), ("applause.mp3", 5.0, 0.14, "hit")],           # struggle->celebration+swell
    11: [("wind_bed.mp3", 0.0, 0.12, "bed"), ("anthem_swell.mp3", 0.0, 0.5, "hit"),
         ("crowd_cheer.mp3", 0.0, 0.1, "bed"), ("fireworks2.mp3", 0.6, 0.3, "hit")],        # finale flag + swell
}

cues, t = [], 0.0
for s in shots:
    d = s["dur"]
    for (f, off, vol, kind) in RECIPE.get(s["id"], []):
        cue = {"_shot": s["id"], "file": f, "at": round(t + off, 3), "vol": vol}
        if kind == "bed":
            cue["trim"] = round(d - off, 3); cue["fadein"] = 0.4; cue["fadeout"] = 0.6
        cues.append(cue)
    t += d

out = {
    "_doc": f"Content-aware foley for the {G} Telangana reel. Times = sec on VO render timeline.",
    "music_vol": 0.06,
    "vo_loudnorm_I": -13 if G == "female" else -12,
    "cues": cues,
}
dst = os.path.join(ROOT, f"sfx_cues_{G}.json")
json.dump(out, open(dst, "w"), ensure_ascii=False, indent=2)
print(f"wrote {dst}  ({len(cues)} cues, reel {t:.1f}s)")
