"""Lab 3 server: guardrails chat page with a model dropdown, port 8000.
Uses only the Python standard library. Run:  python3 server.py
"""
import json
import os
import shutil
import subprocess
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import guardrails

PORT = 8000
HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/models":
            try:
                have = guardrails.installed_models()
            except Exception:
                have = set()
            models = [dict(m, installed=m["name"] in have) for m in guardrails.MODELS]
            return self._send(200, json.dumps({"models": models}))
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/ask":
            return self._send(404, json.dumps({"error": "not found"}))
        model = guardrails.MODEL
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            question = (data.get("question") or "").strip()
            model = data.get("model") or guardrails.MODEL
            if not question:
                return self._send(400, json.dumps({"error": "Type a question first."}))
            if model not in guardrails.MODEL_NAMES:
                return self._send(400, json.dumps({"error": f"Unknown model: {model}"}))
            t0 = time.time()
            result = guardrails.answer(question, model)
            result["seconds"] = round(time.time() - t0, 1)
            print(f"[{model:13}] {result['color']:6} ({result['layer']:5}) {result['seconds']:5}s  {question[:60]}")
            self._send(200, json.dumps(result))
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code == 404:
                msg += f"  ->  Pull it first:  ollama pull {model}"
            self._send(502, json.dumps({"error": f"Ollama error {e.code}: {msg}"}))
        except Exception as e:
            self._send(502, json.dumps({"error": f"Ollama not reachable: {e}. Is 'ollama serve' running?"}))

    def log_message(self, fmt, *args):
        pass


OLLAMA_URL = guardrails.OLLAMA_URL


def ensure_ollama():
    """Start 'ollama serve' in the background if it is not already running."""
    try:
        urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=2)
        print("Ollama is already running on port 11434.")
        return
    except Exception:
        pass
    if not shutil.which("ollama"):
        print("Ollama is not installed. Install it with:  curl -fsSL https://ollama.com/install.sh | sh")
        return
    print("Starting Ollama (ollama serve) on port 11434...")
    subprocess.Popen(["ollama", "serve"], stdout=open("/tmp/ollama.log", "a"),
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(30):
        try:
            urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=2)
            print("Ollama is running.")
            return
        except Exception:
            time.sleep(1)
    print("Ollama did not start - check /tmp/ollama.log")


if __name__ == "__main__":
    ensure_ollama()
    try:
        have = guardrails.installed_models()
        for m in guardrails.MODELS:
            mark = "OK " if m["name"] in have else "-- not pulled"
            print(f"  {mark:14} {m['name']}")
    except Exception:
        pass
    print(f"Lab 3 guardrails chat running on port {PORT} (choose the model in the page)")
    print("Open the PORTS tab and click the globe icon next to port 8000.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
