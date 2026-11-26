"""Verify the URL the monitor prints reaches the run state served by its own socket."""
import json
from http.client import HTTPConnection
from threading import Thread
from urllib.parse import urlsplit

from atlas import monitor


def test_monitor_reports_its_actual_bound_port(tmp_path,monkeypatch,capsys):
    (tmp_path/"progress.json").write_text('{"snapshot":"test-edition","stage":"Complete"}')
    monkeypatch.setattr(monitor,"RESULTS",tmp_path)

    def request_once(server):
        url=urlsplit(capsys.readouterr().out.strip().split()[-1])
        assert url.hostname=="127.0.0.1" and url.port==server.server_port>0
        worker=Thread(target=server.handle_request,daemon=True)
        worker.start()
        conn=HTTPConnection(url.hostname,url.port,timeout=10)
        try:
            conn.request("GET","/progress.json")
            reply=conn.getresponse()
            assert reply.status==200 and json.load(reply)["snapshot"]=="test-edition"
        finally:
            conn.close()
            worker.join(timeout=10)

    monkeypatch.setattr(monitor.ThreadingHTTPServer,"serve_forever",request_once)
    monitor.serve(0)
