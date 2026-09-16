#!/data/data/com.termux/files/home/.local/bin/python
"""pyng.py – Pyng utilities.

This module provides functionality for pyng."""
from __future__ import annotations
import argparse
import re
import subprocess
import sys

class PingResult:
    """PingResult – PingResult."""

    def __init__(self) -> None:
        """__init__ –   init  ."""
        self.host = ''
        self.ip = ''
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_lost = 0
        self.min_time = None
        self.avg_time = None
        self.max_time = None
        self.stddev_time = None
        self.packet_loss_percent = 0.0
        self.responses = []

    def __str__(self) -> str:
        """__str__ –   str  .

Returns:
    str: Description of return value."""
        result = f'\n--- {self.host} ping statistics ---\n'
        result += f'{self.packets_sent} packets transmitted, {self.packets_received} packets received, '
        result += f'{self.packet_loss_percent:.1f}% packet loss\n'
        if self.packets_received > 0:
            result += f'round-trip min/avg/max/stddev = '
            result += f'{self.min_time:.3f}/{self.avg_time:.3f}/{self.max_time:.3f}'
            if self.stddev_time:
                result += f'/{self.stddev_time:.3f}'
            result += ' ms\n'
        return result

def parse_ping_response(output: str) -> PingResult:
    """parse_ping_response – parse ping response.

Args:
    output: Description of output.

Returns:
    PingResult: Description of return value."""
    result = PingResult()
    lines = output.split('\n')
    if lines:
        first_line = lines[0]
        match = re.match('PING\\s+(\\S+)\\s+\\(([^)]+)\\)', first_line)
        if match:
            result.host = match.group(1)
            result.ip = match.group(2)
    for line in lines:
        match = re.search('bytes from.*icmp_seq=(\\d+).*time=([0-9.]+)\\s*ms', line)
        if match:
            result.responses.append({'seq': int(match.group(1)), 'time': float(match.group(2))})
    stats_match = re.search('(\\d+)\\s+packets transmitted,\\s+(\\d+)(?:\\s+packets)?\\s+received,\\s+([0-9.]+)%\\s+packet loss', output)
    if stats_match:
        result.packets_sent = int(stats_match.group(1))
        result.packets_received = int(stats_match.group(2))
        result.packets_lost = result.packets_sent - result.packets_received
        result.packet_loss_percent = float(stats_match.group(3))
    time_match = re.search('min/avg/max(?:/stddev)?\\s*=\\s*([0-9.]+)/([0-9.]+)/([0-9.]+)(?:/([0-9.]+))?', output)
    if time_match:
        result.min_time = float(time_match.group(1))
        result.avg_time = float(time_match.group(2))
        result.max_time = float(time_match.group(3))
        if time_match.group(4):
            result.stddev_time = float(time_match.group(4))
    return result

def ping(host: str, count: int=4, timeout: int=4, packet_size: int=56, verbose: bool=True) -> PingResult | None:
    """ping – ping.

Args:
    host: Description of host.
    count: Description of count.
    timeout: Description of timeout.
    packet_size: Description of packet_size.
    verbose: Description of verbose.

Returns:
    PingResult | None: Description of return value."""
    try:
        cmd = ['ping', '-c', str(count), '-W', str(timeout * 400), '-s', str(packet_size), host]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        output = ''
        if verbose:
            for line in process.stdout:
                print(line.rstrip())
                output += line
        else:
            output, _ = process.communicate()
        process.wait()
        result = parse_ping_response(output)
        return result
    except FileNotFoundError:
        print("Error: 'ping' command not found. Make sure you're on a Unix-like system.")
        return None
    except Exception as e:
        print(f'Error: {e}')
        return None

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Ping a host using ICMP echo requests', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\nExamples:\n  python3 ping.py google.com\n  python3 ping.py -c 10 8.8.8.8\n  python3 ping.py -c 5 -t 2 example.com\n  python3 ping.py -s 128 github.com\n        ')
    parser.add_argument('host', help='Hostname or IP address to ping')
    parser.add_argument('-c', '--count', type=int, default=4, help='Number of ping requests (default: 4)')
    parser.add_argument('-t', '--timeout', type=int, default=4, help='Timeout per request in seconds (default: 4)')
    parser.add_argument('-s', '--size', type=int, default=56, help='ICMP payload size in bytes (default: 56)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode - no output until statistics')
    args = parser.parse_args()
    result = ping(args.host, count=args.count, timeout=args.timeout, packet_size=args.size, verbose=not args.quiet)
    if result:
        print(result)
        sys.exit(0 if result.packet_loss_percent < 100 else 1)
    else:
        sys.exit(1)
if __name__ == '__main__':
    raise SystemExit(main())
