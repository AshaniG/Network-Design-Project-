# Network-Design-Project-

Network design projects built with Cisco Packet Tracer:

- **IOT** – IoT network simulation (`IoT.pkt`)
- **Simple Network Implementation** – SOHO network (`SOHO.pkt`)
- **University Network Project** – University campus network (`University Network.pkt`)

## netcli — command-line tool

A small Python CLI (no dependencies, Python 3.8+) is included in `netcli.py`.

### Web frontend (browser UI)

Start the web frontend and it opens automatically in your browser at
`http://localhost:8000`:

```bash
python3 netcli.py web
```

The page has three cards — Greeting, Packet Tracer project list, and a
Subnet calculator — each backed by a small JSON API served by the same
script. Use `--port` to pick a different port and `--no-browser` to skip
auto-opening the browser. Press `Ctrl+C` in the terminal to stop it.

### Interactive terminal UI

Run the tool with no arguments (or with `ui`) to open a menu-driven interface:

```bash
python3 netcli.py
```

```
+----------------------------------------------+
|        Network Design Project - netcli       |
+----------------------------------------------+
|  1) Greeting                                 |
|  2) List Packet Tracer projects              |
|  3) Subnet calculator                        |
|  4) Exit                                     |
+----------------------------------------------+
```

### Commands

```bash
# Open the interactive menu UI
python3 netcli.py ui

# Print a greeting
python3 netcli.py hello --name Ashani

# List all Packet Tracer project files in the repo
python3 netcli.py list

# Show subnet details for a network in CIDR notation
python3 netcli.py subnet 192.168.1.0/26
```

Run `python3 netcli.py --help` to see all available commands.
