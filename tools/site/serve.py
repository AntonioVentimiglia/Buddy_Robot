#!/usr/bin/env python3
"""Serve a directory over HTTP without ever calling os.getcwd().

    python3 tools/site/serve.py <dir> <port>

Why this exists instead of `python3 -m http.server -d <dir> <port>`:

http.server's command-line entry point builds its argument parser with

    parser.add_argument('--directory', '-d', default=os.getcwd(), ...)

and argparse evaluates that default **eagerly**, at import time — before it ever
looks at the -d you passed. If os.getcwd() raises, the module dies before
serving anything, and passing -d cannot save you.

That is exactly what happens here. This repo lives under
`~/Desktop/Desktop - MacBook Air (263)/`, which is mode drwx------, and the
preview server's process cannot resolve a path for its own working directory:

    PermissionError: [Errno 1] Operation not permitted

The fix is to never ask for the cwd as a *path*. A relative os.chdir() works
through the directory file descriptor without resolving the full path, and
handing the handler an explicit directory keeps it from calling os.getcwd()
itself (SimpleHTTPRequestHandler falls back to os.getcwd() when directory=None).
"""

from __future__ import annotations

import functools
import http.server
import os
import socketserver
import sys


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Same behaviour, minus a log line per asset request."""

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        pass


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    directory, port = sys.argv[1], int(sys.argv[2])

    # Relative chdir resolves through the fd, so it does not need the cwd path.
    os.chdir(directory)

    # directory="." keeps the handler from calling os.getcwd() on its own.
    handler = functools.partial(QuietHandler, directory=".")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"serving {directory} on http://localhost:{port}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
