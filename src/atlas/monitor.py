"""An allowlisted loopback dashboard exposes progress without serving the project directory."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from .io import RESULTS, PACKAGE


def serve(port):
    """Serve the same view that is bundled with the published snapshot."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path in ("/", "/index.html"):
                content, kind = (PACKAGE / "web/progress.html").read_bytes(), "text/html"
            elif path == "/progress.json":
                state = RESULTS / "progress.json"
                content = state.read_bytes() if state.exists() else b'{"stage":"Waiting for a run"}'
                kind = "application/json"
            else:
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type", kind+"; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
    print(f"Live run dashboard http://127.0.0.1:{port}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
