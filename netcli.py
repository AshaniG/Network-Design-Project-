#!/usr/bin/env python3
"""netcli - a simple CLI tool for the Network Design Project repository.

Usage:
    python netcli.py hello [--name NAME]
    python netcli.py list
    python netcli.py subnet <CIDR>

Examples:
    python netcli.py hello --name Ashani
    python netcli.py list
    python netcli.py subnet 192.168.1.0/26
"""

import argparse
import ipaddress
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def cmd_hello(args: argparse.Namespace) -> int:
    """Basic greeting command."""
    print(f"Hello, {args.name}! Welcome to the Network Design Project CLI.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all Packet Tracer project files in the repository."""
    pkt_files = sorted(REPO_ROOT.rglob("*.pkt"))
    if not pkt_files:
        print("No Packet Tracer (.pkt) project files found.")
        return 0

    print(f"Found {len(pkt_files)} network project file(s):\n")
    for pkt in pkt_files:
        rel = pkt.relative_to(REPO_ROOT)
        size_kb = pkt.stat().st_size / 1024
        print(f"  {rel}  ({size_kb:.1f} KB)")
    return 0


def cmd_subnet(args: argparse.Namespace) -> int:
    """Show basic subnet information for a network in CIDR notation."""
    try:
        network = ipaddress.ip_network(args.cidr, strict=False)
    except ValueError as exc:
        print(f"Error: invalid network '{args.cidr}': {exc}", file=sys.stderr)
        return 1

    hosts = list(network.hosts()) if network.num_addresses <= 2 ** 16 else None

    print(f"Network:          {network.network_address}")
    print(f"Netmask:          {network.netmask}")
    print(f"Prefix length:    /{network.prefixlen}")
    print(f"Broadcast:        {network.broadcast_address}")
    print(f"Total addresses:  {network.num_addresses}")
    if hosts is not None and hosts:
        print(f"Usable hosts:     {len(hosts)}")
        print(f"First host:       {hosts[0]}")
        print(f"Last host:        {hosts[-1]}")
    else:
        usable = max(network.num_addresses - 2, 0)
        print(f"Usable hosts:     {usable}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netcli",
        description="CLI tool for the Network Design Project repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
