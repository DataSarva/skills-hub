#!/usr/bin/env python3
"""Local hook trimmer. Serves a browser UI to scrub the IG hook clip and cut the
final ig_hook_trimmed.mp4 (the starting point of the reel). No external deps.

Run:  python3 hook_trimmer/server.py    then open http://127.0.0.1:8770
"""
import http.server, socketserver, os, json, subprocess, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
CLIP = os.path.join(ROOT, "hook", "ig_hook_clean.mp4")   # IG video user sent, text removed
OUT  = os.path.join(ROOT, "hook", "ig_hook_trimmed.mp4")
PORT = 8770

def dur(f):
    try:
        return round(float(subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",f]).decode().strip()),3)
    except Exception:
        return 0.0

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str): body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path.startswith("/clip"):
            self._serve_range(CLIP, "video/mp4")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def _serve_range(self, path, ctype):
        # Range support so the <video> can scrub/seek.
        if not os.path.exists(path):
            self._send(404, json.dumps({"error": "clip missing"})); return
        size = os.path.getsize(path)
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        if rng:
            m = re.match(r"bytes=(\d+)-(\d*)", rng)
            if m:
                start = int(m.group(1))
                if m.group(2): end = int(m.group(2))
        length = end - start + 1
        self.send_response(206 if rng else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start); remaining = length
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): break
                remaining -= len(chunk)

    def do_POST(self):
        if self.path != "/cut":
            self._send(404, json.dumps({"error": "not found"})); return
        n = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
            a = float(data["in"]); b = float(data["out"])
            if b <= a: raise ValueError("out must be > in")
            # frame-accurate re-encode cut, keep audio
            cmd = ["ffmpeg","-y","-ss",f"{a:.3f}","-to",f"{b:.3f}","-i",CLIP,
                   "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
                   "-c:a","aac","-b:a","192k","-avoid_negative_ts","make_zero", OUT]
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode != 0:
                self._send(200, json.dumps({"ok": False, "error": r.stderr.decode()[-300:]})); return
            self._send(200, json.dumps({"ok": True, "dur": dur(OUT)}))
        except Exception as e:
            self._send(200, json.dumps({"ok": False, "error": str(e)}))

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
        print(f"Hook trimmer: http://127.0.0.1:{PORT}  (clip {dur(CLIP)}s)  Ctrl+C to stop")
        httpd.serve_forever()
