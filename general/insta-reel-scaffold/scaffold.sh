#!/usr/bin/env bash
# insta-reel-scaffold — lay down the proven reel harness into a fresh project dir.
# Usage: scaffold.sh <project_dir> [reference_project_for_node_modules]
# Creates: bin/ (pipeline), remotion/ (comp + configs), hook_trimmer/, asset dirs.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DST="${1:?project dir}"; REF="${2:-/Users/aisarva/Downloads/insta_story/flow_parvateesam}"
mkdir -p "$DST"/{bin,clips,clips2,clean_clips,refs,audio_male,audio_female,final_audio_male,final_audio_female,final_clips_male,final_clips_female,sfx,music,covers,storyboard,hook,hook_trimmer,vo_txt,vo_txt_f}
mkdir -p "$DST"/remotion/{src,out,public/music}

cp "$HERE"/assets/bin/* "$DST"/bin/ && chmod +x "$DST"/bin/*.sh 2>/dev/null || true
cp "$HERE"/assets/remotion/src/* "$DST"/remotion/src/
cp "$HERE"/assets/remotion/package.json "$HERE"/assets/remotion/tsconfig.json "$DST"/remotion/
cp "$HERE"/assets/hook_trimmer/* "$DST"/hook_trimmer/
# remotion public symlinks (repointed per gender by make_edition*)
ln -sfn ../../final_audio_male "$DST"/remotion/public/audio
ln -sfn ../../final_clips_male "$DST"/remotion/public/clips

# node_modules: reuse a reference project's to skip a fresh install (429M)
if [ -d "$REF/remotion/node_modules" ] && [ ! -d "$DST/remotion/node_modules" ]; then
  echo "linking node_modules from $REF (run 'npm ci' in remotion/ instead for a clean copy)"
  cp -R "$REF/remotion/node_modules" "$DST"/remotion/node_modules
fi

echo "scaffolded $DST. Next: write shots.json + VO, then bin/make_edition_v2.sh <gender> <VO_X> <out>."
