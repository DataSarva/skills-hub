#!/usr/bin/env bash
set -uo pipefail
P=/Users/aisarva/Downloads/insta_story/grok_agent_telangana
H=/Users/aisarva/Downloads/insta_story/tts_samples/gemini_tts.sh
mood() { case "$1" in 01) echo prompt_hook;; 10|11) echo prompt_climax;; *) echo prompt_body;; esac; }
> $P/vo_durations.txt
for g in male female; do
  if [ "$g" = male ]; then VOICE=Puck; MODEL=gemini-2.5-pro-tts; else VOICE=Leda; MODEL=gemini-2.5-flash-tts; fi
  for n in 01 02 03 04 05 06 07 08 09 10 11; do
    pr=$(mood $n)
    out=$P/audio_$g/b$n.mp3
    dur=$("$H" "$P/vo_txt/b$n.txt" "$out" "$g" "$VOICE" "$MODEL" "$P/vo_txt/$pr.txt" 2>>$P/vo_gen.log)
    echo "$g b$n $dur" | tee -a $P/vo_durations.txt
  done
done
echo "VO DONE"
