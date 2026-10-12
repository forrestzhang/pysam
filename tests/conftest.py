import http.server
import os
import socketserver
import sys
import threading
from pathlib import Path

import pytest


def _build_httpd(directory):
    class QuietHTTPServer(http.server.HTTPServer):
        def server_bind(self):  # Work around actions/runner-images#14568
            socketserver.TCPServer.server_bind(self)
            self.server_name, self.server_port = self.server_address[:2]

        def handle_error(self, request, client_address):
            if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
                pass
            else:
                super().handle_error(request, client_address)

    class QuietRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, format, *args):
            pass

    return QuietHTTPServer(("localhost", 0), QuietRequestHandler)


@pytest.fixture(scope="session")
def httpserver():
    # Spawn safety (Phase 2): the default child-process start method on
    # Windows is spawn, which re-imports this conftest in a child process
    # under pytest's import machinery — slow and fragile.  A daemon thread
    # serves the same localhost ephemeral-port fixture with no child
    # process and no pipe handshake.
    server = _build_httpd(Path(__file__).parent)
    thread = threading.Thread(target=server.serve_forever, name="httpd",
                              daemon=True)
    thread.start()

    yield f"{server.server_name}:{server.server_port}"

    try:
        server.shutdown()
    finally:
        server.server_close()
        thread.join(timeout=10)


def pytest_report_header(config):
    text = []

    if "REF_PATH" in os.environ:
        text.append("pysam: overriding REF_PATH to disable external reference lookups")
    # htslib compiles HTS_PATH_SEPARATOR_CHAR to ';' on _WIN32
    # (htslib/htslib/hts.h:44-51); a literal ':' would be one bogus path
    # entry on Windows rather than an empty element list.  os.pathsep
    # carries the matching separator on every platform.
    os.environ["REF_PATH"] = os.pathsep

    return text
