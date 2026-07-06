#!/usr/bin/env python3
"""netcli - a simple CLI tool for the Network Design Project repository.

Usage:
    python netcli.py                 (opens the interactive menu UI)
    python netcli.py ui
    python netcli.py web [--port PORT]
    python netcli.py hello [--name NAME]
    python netcli.py list
    python netcli.py subnet <CIDR>

Examples:
    python netcli.py web             (opens the browser frontend at http://localhost:8000)
    python netcli.py hello --name Ashani
    python netcli.py list
    python netcli.py subnet 192.168.1.0/26
"""

import argparse
import ipaddress
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Core logic (shared by the CLI commands, the terminal UI, and the web UI)
# ---------------------------------------------------------------------------

def get_projects():
    """Return a list of Packet Tracer project files as dicts."""
    return [
        {
            "path": str(pkt.relative_to(REPO_ROOT)),
            "size_kb": round(pkt.stat().st_size / 1024, 1),
        }
        for pkt in sorted(REPO_ROOT.rglob("*.pkt"))
    ]


def get_subnet_info(cidr: str):
    """Return subnet details for a CIDR network as a dict.

    Raises ValueError for invalid input.
    """
    network = ipaddress.ip_network(cidr, strict=False)
    info = {
        "network": str(network.network_address),
        "netmask": str(network.netmask),
        "prefix_length": network.prefixlen,
        "broadcast": str(network.broadcast_address),
        "total_addresses": network.num_addresses,
    }
    if network.num_addresses <= 2 ** 16:
        hosts = list(network.hosts())
        info["usable_hosts"] = len(hosts)
        if hosts:
            info["first_host"] = str(hosts[0])
            info["last_host"] = str(hosts[-1])
    else:
        info["usable_hosts"] = max(network.num_addresses - 2, 0)
    return info


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_hello(args: argparse.Namespace) -> int:
    """Basic greeting command."""
    print(f"Hello, {args.name}! Welcome to the Network Design Project CLI.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all Packet Tracer project files in the repository."""
    projects = get_projects()
    if not projects:
        print("No Packet Tracer (.pkt) project files found.")
        return 0

    print(f"Found {len(projects)} network project file(s):\n")
    for proj in projects:
        print(f"  {proj['path']}  ({proj['size_kb']} KB)")
    return 0


def cmd_subnet(args: argparse.Namespace) -> int:
    """Show basic subnet information for a network in CIDR notation."""
    try:
        info = get_subnet_info(args.cidr)
    except ValueError as exc:
        print(f"Error: invalid network '{args.cidr}': {exc}", file=sys.stderr)
        return 1

    print(f"Network:          {info['network']}")
    print(f"Netmask:          {info['netmask']}")
    print(f"Prefix length:    /{info['prefix_length']}")
    print(f"Broadcast:        {info['broadcast']}")
    print(f"Total addresses:  {info['total_addresses']}")
    print(f"Usable hosts:     {info['usable_hosts']}")
    if "first_host" in info:
        print(f"First host:       {info['first_host']}")
        print(f"Last host:        {info['last_host']}")
    return 0


# ---------------------------------------------------------------------------
# Terminal menu UI
# ---------------------------------------------------------------------------

MENU = """\
+----------------------------------------------+
|        Network Design Project - netcli       |
+----------------------------------------------+
|  1) Greeting                                 |
|  2) List Packet Tracer projects              |
|  3) Subnet calculator                        |
|  4) Exit                                     |
+----------------------------------------------+"""


def cmd_ui(args: argparse.Namespace) -> int:
    """Interactive menu UI on top of the CLI commands."""
    while True:
        print()
        print(MENU)
        try:
            choice = input("Select an option [1-4]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        print()
        if choice == "1":
            try:
                name = input("Your name (press Enter for default): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                return 0
            cmd_hello(argparse.Namespace(name=name or "there"))
        elif choice == "2":
            cmd_list(args)
        elif choice == "3":
            try:
                cidr = input("Network in CIDR notation (e.g. 192.168.1.0/26): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                return 0
            if cidr:
                cmd_subnet(argparse.Namespace(cidr=cidr))
            else:
                print("No network entered.")
        elif choice == "4" or choice.lower() in ("q", "quit", "exit"):
            print("Goodbye!")
            return 0
        else:
            print(f"Invalid option: '{choice}'. Please choose 1-4.")


# ---------------------------------------------------------------------------
# Web frontend
# ---------------------------------------------------------------------------

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Network Design Project — netcli</title>
<style>
  :root {
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8; --ok: #4ade80;
  }
  * { box-sizing: border-box; margin: 0; }
  body {
    background: var(--bg); color: var(--text); min-height: 100vh;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 2rem 1rem;
  }
  .wrap { max-width: 860px; margin: 0 auto; }
  header { text-align: center; margin-bottom: 2rem; }
  header h1 { font-size: 1.7rem; letter-spacing: .02em; }
  header h1 span { color: var(--accent); }
  header p { color: var(--muted); margin-top: .4rem; }
  .grid { display: grid; gap: 1.2rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.3rem;
  }
  .card h2 { font-size: 1.05rem; margin-bottom: .8rem; color: var(--accent); }
  label { display: block; font-size: .85rem; color: var(--muted); margin-bottom: .3rem; }
  input[type=text] {
    width: 100%; padding: .55rem .7rem; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg); color: var(--text);
    font-size: .95rem; margin-bottom: .7rem;
  }
  input[type=text]:focus { outline: 2px solid var(--accent); border-color: transparent; }
  button {
    background: var(--accent); color: #082f49; border: none; cursor: pointer;
    padding: .55rem 1.1rem; border-radius: 8px; font-weight: 600; font-size: .92rem;
  }
  button:hover { filter: brightness(1.12); }
  .result {
    margin-top: .9rem; font-family: ui-monospace, Menlo, Consolas, monospace;
    font-size: .86rem; white-space: pre-wrap; word-break: break-word;
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; padding: .8rem; min-height: 2.4rem; color: var(--ok);
  }
  .result.error { color: #f87171; }
  footer { text-align: center; color: var(--muted); font-size: .8rem; margin-top: 2rem; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Network Design Project — <span>netcli</span></h1>
    <p>Web frontend for the netcli command-line tool</p>
  </header>

  <div class="grid">
    <div class="card">
      <h2>1 · Greeting</h2>
      <label for="name">Your name</label>
      <input type="text" id="name" placeholder="Ashani">
      <button onclick="hello()">Say hello</button>
      <div class="result" id="hello-out"></div>
    </div>

    <div class="card">
      <h2>2 · Packet Tracer projects</h2>
      <p style="color:var(--muted);font-size:.85rem;margin-bottom:.7rem">
        Lists every .pkt project file found in this repository.
      </p>
      <button onclick="listProjects()">List projects</button>
      <div class="result" id="list-out"></div>
    </div>

    <div class="card">
      <h2>3 · Subnet calculator</h2>
      <label for="cidr">Network (CIDR notation)</label>
      <input type="text" id="cidr" placeholder="192.168.1.0/26">
      <button onclick="subnet()">Calculate</button>
      <div class="result" id="subnet-out"></div>
    </div>
  </div>

  <footer>netcli · Python standard library only · Ctrl+C in the terminal to stop the server</footer>
</div>

<script>
async function call(url, outId, render) {
  const out = document.getElementById(outId);
  out.classList.remove('error');
  out.textContent = 'Loading…';
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    out.textContent = render(data);
  } catch (err) {
    out.classList.add('error');
    out.textContent = 'Error: ' + err.message;
  }
}

function hello() {
  const name = document.getElementById('name').value.trim();
  call('/api/hello?name=' + encodeURIComponent(name), 'hello-out', d => d.message);
}

function listProjects() {
  call('/api/projects', 'list-out', d => {
    if (!d.projects.length) return 'No .pkt project files found.';
    return d.projects.map(p => p.path + '  (' + p.size_kb + ' KB)').join('\\n');
  });
}

function subnet() {
  const cidr = document.getElementById('cidr').value.trim();
  call('/api/subnet?cidr=' + encodeURIComponent(cidr), 'subnet-out', d => {
    const lines = [
      'Network:         ' + d.network,
      'Netmask:         ' + d.netmask,
      'Prefix length:   /' + d.prefix_length,
      'Broadcast:       ' + d.broadcast,
      'Total addresses: ' + d.total_addresses,
      'Usable hosts:    ' + d.usable_hosts,
    ];
    if (d.first_host) {
      lines.push('First host:      ' + d.first_host);
      lines.push('Last host:       ' + d.last_host);
    }
    return lines.join('\\n');
  });
}

document.getElementById('cidr').addEventListener('keydown', e => { if (e.key === 'Enter') subnet(); });
document.getElementById('name').addEventListener('keydown', e => { if (e.key === 'Enter') hello(); });
</script>
</body>
</html>
"""


class NetcliHandler(BaseHTTPRequestHandler):
    """Serves the single-page frontend and its small JSON API."""

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path in ("/", "/index.html"):
            self._send(200, INDEX_HTML.encode(), "text/html; charset=utf-8")
        elif parsed.path == "/api/hello":
            name = query.get("name", [""])[0].strip() or "there"
            self._send_json(200, {
                "message": f"Hello, {name}! Welcome to the Network Design Project CLI."
            })
        elif parsed.path == "/api/projects":
            self._send_json(200, {"projects": get_projects()})
        elif parsed.path == "/api/subnet":
            cidr = query.get("cidr", [""])[0].strip()
            if not cidr:
                self._send_json(400, {"error": "missing 'cidr' parameter"})
                return
            try:
                self._send_json(200, get_subnet_info(cidr))
            except ValueError as exc:
                self._send_json(400, {"error": f"invalid network '{cidr}': {exc}"})
        else:
            self._send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # quieter default logging
        sys.stderr.write("[web] %s\n" % (fmt % args))


def cmd_web(args: argparse.Namespace) -> int:
    """Serve the browser frontend on localhost."""
    server = HTTPServer(("127.0.0.1", args.port), NetcliHandler)
    url = f"http://localhost:{args.port}"
    print(f"netcli web frontend running at {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
    return 0


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netcli",
        description="CLI tool for the Network Design Project repository.",
    )
    subparsers = parser.add_subparsers(dest="command")

    ui = subparsers.add_parser("ui", help="Open the interactive terminal menu UI")
    ui.set_defaults(func=cmd_ui)

    web = subparsers.add_parser("web", help="Open the browser web frontend")
    web.add_argument("--port", type=int, default=8000, help="Port to serve on (default 8000)")
    web.add_argument("--no-browser", action="store_true",
                     help="Don't open the browser automatically")
    web.set_defaults(func=cmd_web)

    hello = subparsers.add_parser("hello", help="Print a greeting")
    hello.add_argument("--name", default="there", help="Name to greet")
    hello.set_defaults(func=cmd_hello)

    lister = subparsers.add_parser("list", help="List Packet Tracer project files")
    lister.set_defaults(func=cmd_list)

    subnet = subparsers.add_parser("subnet", help="Show subnet info for a CIDR network")
    subnet.add_argument("cidr", help="Network in CIDR notation, e.g. 192.168.1.0/26")
    subnet.set_defaults(func=cmd_subnet)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command is None:
        return cmd_ui(args)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
