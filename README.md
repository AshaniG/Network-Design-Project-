# Network-Design-Project-

Network design projects built with Cisco Packet Tracer:

- **IOT** – IoT network simulation (`IoT.pkt`)
- **Simple Network Implementation** – SOHO network (`SOHO.pkt`)
- **University Network Project** – University campus network (`University Network.pkt`)

## netcli — command-line tool

A small Python CLI (no dependencies, Python 3.8+) is included in `netcli.py`.

### Commands

```bash
# Print a greeting
python3 netcli.py hello --name Ashani

# List all Packet Tracer project files in the repo
python3 netcli.py list

# Show subnet details for a network in CIDR notation
python3 netcli.py subnet 192.168.1.0/26
```

Run `python3 netcli.py --help` to see all available commands.
