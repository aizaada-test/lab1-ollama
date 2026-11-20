"""Lab 2 server: guardrails chat page on port 8000.
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
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/ask":
            return self._send(404, json.dumps({"error": "not found"}))
        try:
            length = int(self.headers.get("Content-Length", 0))
            question = (json.loads(self.rfile.read(length) or b"{}").get("question") or "").strip()
            if not question:
                return self._send(400, json.dumps({"error": "Type a question first."}))
            result = guardrails.answer(question)
            print(f"[guardrails] {result['color']:6} ({result['layer']}) {question[:70]}")
            self._send(200, json.dumps(result))
        except urllib.error.HTTPError as e:
            self._send(502, json.dumps({"error": f"Ollama error {e.code}: {e.read().decode()[:300]}"}))
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
    print(f"Guardrails chat running on port {PORT} (model: {guardrails.MODEL})")
    print("Open the PORTS tab and click the globe icon next to port 8000.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
