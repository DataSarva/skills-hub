#!/usr/bin/env python3
"""Multi-clip-per-beat rebuild: speed each beat's VO by VO_X, then fit its clip(s) to the VO.
A beat can list several clips ("clips": [...]) — the beat's VO time is split evenly across them,
so long beats show 2+ faster cuts instead of one slow-mo shot.

Env: SHOTS, AUDIO_DIR, FINAL_AUDIO, FINAL_CLIPS, SRC_DIR(=clean_clips), VO_X(=1.31), BREATH(=0.15)
Writes per-beat sped VO + fitted segment clips, and updates SHOTS with segments/dur/vo_dur.
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.environ["SHOTS"]; AUD = os.environ["AUDIO_DIR"]
FA = os.environ["FINAL_AUDIO"]; FC = os.environ["FINAL_CLIPS"]
SRC = os.path.join(ROOT, os.environ.get("SRC_DIR", "clean_clips"))
VO_X = float(os.environ.get("VO_X", "1.31")); BREATH = float(os.environ.get("BREATH", "0.15"))
os.makedirs(FA, exist_ok=True); os.makedirs(FC, exist_ok=True)

def dur(f):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nk=1:nw=1", f]).decode().strip())

d = json.load(open(SHOTS))
for s in d["shots"]:
    sid = s["id"]
    raw = os.path.join(AUD, f"shot{sid}.mp3"); fa = os.path.join(FA, f"shot{sid}.mp3")
    subprocess.run(["ffmpeg","-y","-i",raw,"-filter:a",f"atempo={VO_X}",fa],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    vo = dur(fa); target = vo + BREATH
    clips = s.get("clips", [f"shot{sid}"]); n = len(clips)
    seg_target = target / n
    segs = []
    for k, name in enumerate(clips):
        src = os.path.join(SRC, f"{name}.mp4")
        mult = seg_target / dur(src)
        out = os.path.join(FC, f"{sid}_{k}.mp4")
        subprocess.run(["ffmpeg","-y","-i",src,"-filter:v",f"setpts=PTS*{mult}","-an",
            "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-r","30", out],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        segs.append({"clip": f"{sid}_{k}", "dur": round(dur(out), 3)})
    s["segments"] = segs
    s["vo_dur"] = round(vo, 3)
    s["dur"] = round(sum(x["dur"] for x in segs), 3)
    print(f"shot{sid}: vo={vo:.2f}s {n} seg(s) -> {s['dur']:.2f}s  [{', '.join(clips)}]")

json.dump(d, open(SHOTS, "w"), ensure_ascii=False, indent=2)
print(f"total reel: {sum(s['dur'] for s in d['shots']):.1f}s  VO sum: {sum(s['vo_dur'] for s in d['shots']):.1f}s")
