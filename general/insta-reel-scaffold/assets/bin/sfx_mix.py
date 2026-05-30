#!/usr/bin/env python3
"""Frame-accurate SFX foley mixer for the parvateesam reel.

Reads sfx_cues.json (cue list with per-cue file/at/vol/trim/fades), mixes them over the
VO render + music bed, loudness-normalizes the VO, and writes an IG-spec mp4.

Usage:
  bin/sfx_mix.py <vo_video.mp4> <music.wav> <out.mp4> [cues.json]

Cue fields: file (in sfx/), at (sec), vol, optional trim (sec, makes it a bed), fadein, fadeout.
One-shots (no trim) play their natural length. Times are seconds on the VO render timeline.
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VO   = sys.argv[1]
MUS  = sys.argv[2]
OUT  = sys.argv[3]
CUES = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, "sfx_cues.json")
SFX  = os.path.join(ROOT, "sfx")

cfg = json.load(open(CUES))
cues = [c for c in cfg["cues"]]
music_vol = cfg.get("music_vol", 0.05)
vo_I = cfg.get("vo_loudnorm_I", -13)

inputs = ["-i", VO, "-stream_loop", "-1", "-i", MUS]
parts = [f"[0:a]loudnorm=I={vo_I}:TP=-1.0:LRA=11[vo]",
         f"[1:a]volume={music_vol}[mus]"]
labels = ["[vo]", "[mus]"]

idx = 2  # next input index
for n, c in enumerate(cues):
    f = os.path.join(SFX, c["file"])
    if not os.path.exists(f):
        sys.stderr.write(f"WARN missing {f}, skipping cue {n}\n"); continue
    inputs += ["-i", f]
    chain = [f"[{idx}:a]"]
    if "trim" in c:
        chain.append(f"atrim=0:{c['trim']}")
    fi = c.get("fadein", 0); fo = c.get("fadeout", 0)
    if fi: chain.append(f"afade=t=in:st=0:d={fi}")
    if fo:
        end = c.get("trim")
        st = (end - fo) if end else None
        if st is not None:
            chain.append(f"afade=t=out:st={max(0,st)}:d={fo}")
    chain.append(f"volume={c['vol']}")
    ms = int(round(c["at"] * 1000))
    chain.append(f"adelay={ms}|{ms}")
    lab = f"[c{n}]"
    parts.append("".join(chain[:1]) + ",".join(chain[1:]) + lab)
    labels.append(lab)
    idx += 1

mix = "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first:dropout_transition=0,alimiter=limit=0.97,aresample=48000[a]"
parts.append(mix)
fc = ";".join(parts)

cmd = ["ffmpeg", "-y", *inputs,
       "-filter_complex", fc,
       "-map", "0:v", "-map", "[a]",
       "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
       "-pix_fmt", "yuv420p", "-color_range", "tv", "-r", "30", "-crf", "19", "-preset", "medium",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", OUT]
print(f"mixing {len(labels)} tracks ({len(cues)} cues) -> {OUT}")
r = subprocess.run(cmd, stderr=subprocess.PIPE)
if r.returncode != 0:
    sys.stderr.write(r.stderr.decode()[-1500:]); sys.exit(1)
print("OK")
