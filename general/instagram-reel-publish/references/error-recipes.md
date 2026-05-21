# instagram-reel-publish — error recipes

Verbatim fix sequences for the most common upload failures. Try in order.

---

## 1. `LoginRequired` / `ChallengeRequired`

Cause: `.instagram_session.json` is stale OR Instagram flagged a "new device" challenge.

```bash
cd ~/Documents/insta_ai_vid

# Step 1: drop cached session
rm -f .instagram_session.json

# Step 2: retry upload (will re-login fresh)
iex contentgen -- python3 lib/platforms/instagram_upload.py \
  --video <reel.mp4> --caption-file <caption.json>
```

If the retry STILL fails with `ChallengeRequired`:

1. Open Instagram on your phone (same network).
2. Open the @aisarva_ account.
3. Acknowledge any "Suspicious login attempt" notification.
4. Wait 60 seconds.
5. Re-run the upload.

If it still fails after that, IG has flagged the IP for automation. Wait 24h before retrying.

---

## 2. `ClientError: feedback_required` (soft ban)

Cause: posted too many reels too quickly, or hit a content-similarity flag.

```bash
# Wait at least 30 min. Confirm wait by checking timestamp:
date -v+30M +%H:%M

# Then retry once. If it fails again, wait 6 hours.
```

Prevention: never post >3 reels in a 30-min window; never post the same caption twice; vary the cover image even if reposting near-identical content.

---

## 3. `MediaError: invalid format` (rejected by IG server)

Cause: video doesn't meet Reels spec (codec, resolution, missing audio, etc).

```bash
# Step 1: validate
bash ~/.skills-hub/general/instagram-reel-publish/scripts/validate_reel.sh <reel.mp4>

# Step 2: if anything FAILed, re-encode to a known-good profile
ffmpeg -y -i <input.mp4> \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1" \
  -r 30 -c:v libx264 -profile:v high -level 4.0 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -ar 44100 \
  -movflags +faststart \
  <output_normalized.mp4>

# Step 3: re-validate
bash ~/.skills-hub/general/instagram-reel-publish/scripts/validate_reel.sh <output_normalized.mp4>

# Step 4: upload the normalized file
```

If the input has no audio at all, add a silent stereo AAC track BEFORE the normalize step:

```bash
ffmpeg -y -i <input.mp4> -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=44100" \
  -shortest -c:v copy -c:a aac -b:a 128k -movflags +faststart \
  <input_with_silent_audio.mp4>
```

---

## 4. `ClientError: 2fa_required`

Cause: 2FA is enabled on the account. instagrapi CANNOT complete TOTP automatically.

**Fix:** disable 2FA on @aisarva_ via Settings → Privacy and Security → Two-factor authentication. This is a documented instagrapi limitation. There is no scripted workaround for the free / unofficial API.

(For business accounts using the Graph API, 2FA works — but Graph API requires app review which we have not done for this account.)

---

## 5. Caption shows literal `{...}` instead of rendered text

Cause: you passed JSON to `--caption` (which expects a plain string).

**Wrong:**

```bash
--caption '{"logline":"hello","hashtags":["#test"]}'
```

**Right:**

```bash
--caption-file path/to/caption.json
# OR
--caption "హలో! ఇది ఒక రీల్. #Telugu #Reels"
```

---

## 6. Upload hangs > 5 min with no progress

Cause: IG throttling new-device or low-trust account.

```bash
# 1. Cancel (Ctrl-C)
# 2. Wait 1 hour
# 3. Open the IG mobile app on the account once (clears shadow-flags)
# 4. Retry upload once. If it hangs again, treat as soft ban (recipe #2) — wait 24h.
```

Never retry-loop a hanging upload. Each hung attempt deepens IG's throttle on the account.
