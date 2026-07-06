# Network-Design-Project-

Cisco Packet Tracer network design projects:

- **IOT** — IoT network (`IOT/IoT.pkt`)
- **Simple Network Implementation** — SOHO network (`Simple Network Implementation/SOHO.pkt`)
- **University Network Project** — campus network (`University Network Project/University Network.pkt`)

## Network Design Toolkit CLI

A simple command-line tool with an interactive terminal UI for common
network design tasks. Requires only Python 3.8+ (no dependencies).

### Interactive UI

```bash
python3 cli/network_cli.py
```

Opens a menu with:

1. **Subnet calculator** — network/broadcast address, masks, usable host range
2. **IP address info** — class, binary form, private/public scope
3. **VLSM planner** — split a network to fit multiple host requirements
4. **Browse projects** — list the `.pkt` files in this repository

### One-shot commands

```bash
python3 cli/network_cli.py subnet 192.168.1.0/26
python3 cli/network_cli.py ipinfo 10.0.0.5
python3 cli/network_cli.py vlsm 192.168.1.0/24 60 30 10 2
python3 cli/network_cli.py projects
```
