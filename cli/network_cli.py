#!/usr/bin/env python3
"""Network Design Toolkit — a simple CLI with an interactive terminal UI.

Companion tool for the Packet Tracer projects in this repository.
Runs on Python 3.8+ with no third-party dependencies.

Usage:
    python3 network_cli.py              # interactive menu UI
    python3 network_cli.py subnet 192.168.1.0/26
    python3 network_cli.py ipinfo 10.0.0.5
    python3 network_cli.py vlsm 192.168.1.0/24 60 30 10 2
    python3 network_cli.py projects
"""

import argparse
import ipaddress
import os
import sys

# ---------------------------------------------------------------------------
# Terminal UI helpers
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


class Style:
    enabled = _supports_color()

    @classmethod
    def _wrap(cls, code: str, text: str) -> str:
        if not cls.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    @classmethod
    def bold(cls, t): return cls._wrap("1", t)
    @classmethod
    def dim(cls, t): return cls._wrap("2", t)
    @classmethod
    def cyan(cls, t): return cls._wrap("36", t)
    @classmethod
    def green(cls, t): return cls._wrap("32", t)
    @classmethod
    def yellow(cls, t): return cls._wrap("33", t)
    @classmethod
    def red(cls, t): return cls._wrap("31", t)
    @classmethod
    def blue(cls, t): return cls._wrap("34", t)


WIDTH = 62


def banner():
    line = "═" * WIDTH
    title = "NETWORK DESIGN TOOLKIT"
    subtitle = "Subnetting · IP analysis · VLSM · Project browser"
    print(Style.cyan(f"╔{line}╗"))
    print(Style.cyan("║") + Style.bold(title.center(WIDTH)) + Style.cyan("║"))
    print(Style.cyan("║") + Style.dim(subtitle.center(WIDTH)) + Style.cyan("║"))
    print(Style.cyan(f"╚{line}╝"))


def section(title: str):
    print()
    print(Style.blue("┌─ ") + Style.bold(title) + Style.blue(" " + "─" * max(0, WIDTH - len(title) - 4)))


def row(label: str, value: str):
    if len(label) > 21:
        label = label[:20] + "…"
    print(Style.blue("│ ") + Style.dim(f"{label:<22}") + str(value))


def section_end():
    print(Style.blue("└" + "─" * WIDTH))


def error(msg: str):
    print(Style.red(f"  ✗ {msg}"))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def subnet_report(cidr: str) -> bool:
    """Print a full report for a network in CIDR notation."""
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        error(f"Invalid network: {exc}")
        return False

    hosts = net.num_addresses - 2 if net.version == 4 and net.prefixlen < 31 else net.num_addresses
    section(f"Subnet report for {net.with_prefixlen}")
    row("Network address", str(net.network_address))
    row("Broadcast address", str(net.broadcast_address) if net.version == 4 else "n/a (IPv6)")
    row("Subnet mask", str(net.netmask))
    row("Wildcard mask", str(net.hostmask))
    row("Prefix length", f"/{net.prefixlen}")
    row("Total addresses", f"{net.num_addresses:,}")
    row("Usable hosts", f"{max(hosts, 0):,}")
    if net.version == 4 and net.prefixlen < 31:
        row("First usable host", str(net.network_address + 1))
        row("Last usable host", str(net.broadcast_address - 1))
    row("Private network", "yes" if net.is_private else "no")
    section_end()
    return True


def ip_info(addr: str) -> bool:
    """Print classification details for a single IP address."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError as exc:
        error(f"Invalid IP address: {exc}")
        return False

    section(f"IP address info for {ip}")
    row("Version", f"IPv{ip.version}")
    if ip.version == 4:
        first_octet = int(str(ip).split(".")[0])
        if first_octet < 128:
            ip_class, default_mask = "A", "255.0.0.0"
        elif first_octet < 192:
            ip_class, default_mask = "B", "255.255.0.0"
        elif first_octet < 224:
            ip_class, default_mask = "C", "255.255.255.0"
        elif first_octet < 240:
            ip_class, default_mask = "D (multicast)", "n/a"
        else:
            ip_class, default_mask = "E (experimental)", "n/a"
        row("Class", ip_class)
        row("Default mask", default_mask)
        row("Binary", ".".join(f"{int(o):08b}" for o in str(ip).split(".")))
    row("Private", "yes" if ip.is_private else "no")
    row("Loopback", "yes" if ip.is_loopback else "no")
    row("Multicast", "yes" if ip.is_multicast else "no")
    row("Link-local", "yes" if ip.is_link_local else "no")
    row("Globally routable", "yes" if ip.is_global else "no")
    section_end()
    return True


def vlsm_plan(base_cidr: str, host_counts) -> bool:
    """Allocate subnets for the given host requirements using VLSM."""
    try:
        base = ipaddress.ip_network(base_cidr, strict=False)
    except ValueError as exc:
        error(f"Invalid base network: {exc}")
        return False
    if base.version != 4:
        error("VLSM planner supports IPv4 networks only.")
        return False

    try:
        needs = sorted((int(h) for h in host_counts), reverse=True)
    except ValueError:
        error("Host counts must be integers.")
        return False
    if not needs or any(h < 1 for h in needs):
        error("Provide at least one host count of 1 or more.")
        return False

    section(f"VLSM plan for {base.with_prefixlen}")
    cursor = base.network_address
    allocations = []
    for hosts in needs:
        size = hosts + 2  # network + broadcast
        prefix = 32
        while (1 << (32 - prefix)) < size:
            prefix -= 1
        try:
            subnet = ipaddress.ip_network(f"{cursor}/{prefix}", strict=True)
        except ValueError:
            # Align cursor up to the subnet boundary.
            block = 1 << (32 - prefix)
            aligned = (int(cursor) + block - 1) // block * block
            subnet = ipaddress.ip_network((aligned, prefix))
        if subnet.broadcast_address > base.broadcast_address or subnet.network_address < base.network_address:
            section_end()
            error(f"Ran out of space: cannot fit a subnet for {hosts} hosts in {base}.")
            return False
        allocations.append((hosts, subnet))
        cursor = subnet.broadcast_address + 1

    for i, (hosts, subnet) in enumerate(allocations, 1):
        usable = subnet.num_addresses - 2
        row(f"Subnet {i} ({hosts} hosts)",
            f"{subnet.with_prefixlen}  mask {subnet.netmask}  ({usable} usable)")
    remaining = int(base.broadcast_address) - int(cursor) + 1
    row("Addresses left over", f"{max(remaining, 0):,}")
    section_end()
    return True


def list_projects(repo_root: str) -> bool:
    """List the Packet Tracer project files found in the repository."""
    section("Packet Tracer projects in this repository")
    found = False
    for dirpath, _dirnames, filenames in sorted(os.walk(repo_root)):
        if ".git" in dirpath:
            continue
        for name in sorted(filenames):
            if name.lower().endswith(".pkt"):
                found = True
                rel = os.path.relpath(os.path.join(dirpath, name), repo_root)
                size_kb = os.path.getsize(os.path.join(dirpath, name)) / 1024
                row(os.path.basename(os.path.dirname(rel)) or ".", f"{rel}  ({size_kb:.0f} KB)")
    if not found:
        row("(none found)", "no .pkt files under " + repo_root)
    section_end()
    return True


# ---------------------------------------------------------------------------
# Interactive menu UI
# ---------------------------------------------------------------------------

MENU = [
    ("1", "Subnet calculator", "Full report for a network, e.g. 192.168.1.0/26"),
    ("2", "IP address info", "Class, binary form, and scope of an address"),
    ("3", "VLSM planner", "Split a network for multiple host requirements"),
    ("4", "Browse projects", "List the .pkt files in this repository"),
    ("q", "Quit", ""),
]


def print_menu():
    section("Main menu")
    for key, name, desc in MENU:
        hint = Style.dim(f"  — {desc}") if desc else ""
        print(Style.blue("│ ") + Style.yellow(f"[{key}]") + f" {Style.bold(name)}{hint}")
    section_end()


def prompt(text: str) -> str:
    try:
        return input(Style.green(f"  {text} ❯ ")).strip()
    except EOFError:
        return "q"


def interactive(repo_root: str):
    banner()
    while True:
        print_menu()
        choice = prompt("Select an option").lower()
        if choice in ("q", "quit", "exit"):
            print(Style.dim("\n  Goodbye!\n"))
            return
        elif choice == "1":
            cidr = prompt("Network (CIDR, e.g. 192.168.1.0/26)")
            if cidr:
                subnet_report(cidr)
        elif choice == "2":
            addr = prompt("IP address (e.g. 10.0.0.5)")
            if addr:
                ip_info(addr)
        elif choice == "3":
            base = prompt("Base network (e.g. 192.168.1.0/24)")
            counts = prompt("Host counts, space-separated (e.g. 60 30 10 2)")
            if base and counts:
                vlsm_plan(base, counts.split())
        elif choice == "4":
            list_projects(repo_root)
        elif choice:
            error(f"Unknown option: {choice!r}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    parser = argparse.ArgumentParser(
        prog="network_cli",
        description="Network Design Toolkit — interactive UI and one-shot commands.",
    )
    sub = parser.add_subparsers(dest="command")

    p_subnet = sub.add_parser("subnet", help="Subnet report for a CIDR network")
    p_subnet.add_argument("cidr", help="Network in CIDR notation, e.g. 192.168.1.0/26")

    p_ip = sub.add_parser("ipinfo", help="Details about a single IP address")
    p_ip.add_argument("address", help="IP address, e.g. 10.0.0.5")

    p_vlsm = sub.add_parser("vlsm", help="VLSM plan for multiple host requirements")
    p_vlsm.add_argument("base", help="Base network, e.g. 192.168.1.0/24")
    p_vlsm.add_argument("hosts", nargs="+", help="Required host counts, e.g. 60 30 10 2")

    sub.add_parser("projects", help="List Packet Tracer projects in the repository")

    args = parser.parse_args(argv)

    if args.command is None:
        interactive(repo_root)
        return 0
    if args.command == "subnet":
        return 0 if subnet_report(args.cidr) else 1
    if args.command == "ipinfo":
        return 0 if ip_info(args.address) else 1
    if args.command == "vlsm":
        return 0 if vlsm_plan(args.base, args.hosts) else 1
    if args.command == "projects":
        return 0 if list_projects(repo_root) else 1
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(130)
