#!/usr/bin/env python3
"""
WiFi Checker - Console utility for internet diagnostics
Author: itzlazzy
"""

import os
import sys
import socket
import subprocess
import platform
import time
import json
import re
import webbrowser
from datetime import datetime

# Attempt to import speedtest-cli
try:
    import speedtest
except ImportError:
    print("[!] Installing speedtest-cli...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "speedtest-cli"])
    import speedtest

# ANSI colors for styling
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'


BOX_WIDTH = 58
BORDER_COLOR = Colors.CYAN


# ---------------------------------------------------------------------------
# Small UI toolkit (box drawing helpers)
# ---------------------------------------------------------------------------

def clear_screen():
    """Clear screen"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def box_top(width=BOX_WIDTH, color=BORDER_COLOR):
    return f"{color}╔{'═' * (width - 2)}╗{Colors.END}"


def box_bottom(width=BOX_WIDTH, color=BORDER_COLOR):
    return f"{color}╚{'═' * (width - 2)}╝{Colors.END}"


def box_divider(width=BOX_WIDTH, color=BORDER_COLOR):
    return f"{color}╠{'═' * (width - 2)}╣{Colors.END}"


def box_title(title, width=BOX_WIDTH, color=BORDER_COLOR, title_color=Colors.BOLD + Colors.WHITE):
    inner = width - 2
    pad = max(0, inner - len(title))
    left = pad // 2
    right = pad - left
    return f"{color}║{Colors.END}{' ' * left}{title_color}{title}{Colors.END}{' ' * right}{color}║{Colors.END}"


def box_empty(width=BOX_WIDTH, color=BORDER_COLOR):
    return f"{color}║{Colors.END}{' ' * (width - 2)}{color}║{Colors.END}"


def box_line(plain_text, colored_text=None, width=BOX_WIDTH, color=BORDER_COLOR, align='left'):
    """A single content row inside a box. `plain_text` is used to compute
    padding correctly (ANSI codes don't count towards visible width),
    `colored_text` (if given) is what actually gets printed."""
    if colored_text is None:
        colored_text = plain_text
    inner = width - 4  # 2 border chars + 1 space padding each side
    pad = max(0, inner - len(plain_text))
    if align == 'center':
        left = pad // 2
        right = pad - left
        return f"{color}║{Colors.END} {' ' * left}{colored_text}{' ' * right} {color}║{Colors.END}"
    return f"{color}║{Colors.END} {colored_text}{' ' * pad} {color}║{Colors.END}"


def print_box(lines, title=None, width=BOX_WIDTH, color=BORDER_COLOR):
    """Print a full box. `lines` is a list of (plain, colored) tuples or plain strings."""
    print(box_top(width, color))
    if title:
        print(box_title(title, width, color))
        print(box_divider(width, color))
    for line in lines:
        if line is None:
            print(box_empty(width, color))
        elif isinstance(line, tuple):
            print(box_line(line[0], line[1], width, color))
        else:
            print(box_line(line, line, width, color))
    print(box_bottom(width, color))


def section_header(icon, text):
    """Boxed header used before each diagnostic action."""
    print_box([(f"{icon}  {text}", f"{Colors.BOLD}{Colors.YELLOW}{icon}  {text}{Colors.END}")],
              width=BOX_WIDTH, color=BORDER_COLOR)
    print()


def row(label, value, value_color=Colors.WHITE, label_width=20):
    """A neatly aligned 'Label ......... value' console row (used outside boxes)."""
    dots = '.' * max(1, label_width - len(label))
    print(f"  {Colors.GREEN}✓{Colors.END} {Colors.BOLD}{label}{Colors.END} {Colors.GRAY}{dots}{Colors.END} {value_color}{value}{Colors.END}")


def row_fail(label, message="Unavailable"):
    print(f"  {Colors.RED}✗{Colors.END} {Colors.BOLD}{label}{Colors.END} {Colors.RED}{message}{Colors.END}")


def wait_for_enter():
    print()
    input(f"  {Colors.GRAY}Press [Enter] to return to the menu...{Colors.END}")


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def print_banner():
    """Print banner"""
    logo_lines = [
        "╦ ╦ ╔═╗ ╔═╗  ╔═╗ ╦ ╦ ╔═╗ ╔═╗ ╦╔═ ╔═╗ ╦═╗",
        "║║║ ╠╣  ╠╣   ║   ╠═╣ ║╣  ║   ╠╩╗ ║╣  ╠╦╝",
        "╚╩╝ ╚   ╚    ╚═╝ ╩ ╩ ╚═╝ ╚═╝ ╩ ╚ ╚═╝ ╩╚═",
    ]
    print()
    print(box_top())
    for line in logo_lines:
        print(box_line(line, f"{Colors.BOLD}{Colors.CYAN}{line}{Colors.END}", align='center'))
    print(box_empty())
    print(box_line("WiFi Checker  v1.0", f"{Colors.GREEN}{Colors.BOLD}WiFi Checker{Colors.END}  {Colors.GRAY}v1.0{Colors.END}", align='center'))
    print(box_line("by itzlazzy", f"{Colors.YELLOW}by itzlazzy{Colors.END}", align='center'))
    print(box_bottom())
    print()


# ---------------------------------------------------------------------------
# Diagnostic functions
# ---------------------------------------------------------------------------

def get_ip_info():
    """Get IP address information"""
    section_header("🌐", "IP & ISP INFORMATION")

    # Local IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        row("Local hostname", hostname)
        row("Local IP", local_ip)
    except Exception as e:
        row_fail("Local IP", str(e))

    print()

    # External IP
    try:
        import urllib.request
        external_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        row("External IP", external_ip, Colors.CYAN)

        # Additional IP info
        try:
            response = urllib.request.urlopen(f'http://ip-api.com/json/{external_ip}').read()
            ip_data = json.loads(response)

            if ip_data.get('status') == 'success':
                print()
                row("ISP", ip_data.get('isp', 'Unknown'))
                row("City", ip_data.get('city', 'Unknown'))
                row("Country", ip_data.get('country', 'Unknown'))
                row("Region", ip_data.get('regionName', 'Unknown'))
                row("Timezone", ip_data.get('timezone', 'Unknown'))
                row("Coordinates", f"{ip_data.get('lat', '?')}, {ip_data.get('lon', '?')}")
        except Exception:
            print(f"\n  {Colors.YELLOW}! Additional information unavailable{Colors.END}")

    except Exception as e:
        row_fail("External IP", str(e))

    return local_ip if 'local_ip' in locals() else None


def get_network_stats():
    """Get network statistics"""
    section_header("📶", "WIFI STATISTICS")

    system = platform.system()

    try:
        if system == "Windows":
            # WiFi information
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'],
                                     capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'SSID' in line and 'BSSID' not in line:
                        row("SSID", line.split(':', 1)[1].strip())
                    elif 'BSSID' in line:
                        row("BSSID", line.split(':', 1)[1].strip())
                    elif 'Radio type' in line:
                        row("Network type", line.split(':', 1)[1].strip())
                    elif 'Channel' in line:
                        row("Channel", line.split(':', 1)[1].strip())
                    elif 'Receive rate' in line:
                        row("Receive rate", f"{line.split(':', 1)[1].strip()} Mbps")
                    elif 'Transmit rate' in line:
                        row("Transmit rate", f"{line.split(':', 1)[1].strip()} Mbps")
                    elif 'Signal' in line:
                        try:
                            signal = line.split(':', 1)[1].strip().replace('%', '')
                            signal_int = int(signal)
                            signal_bars = "▓" * (signal_int // 20) + "░" * (5 - signal_int // 20)
                            row("Signal", f"{signal_int}%  {Colors.CYAN}[{signal_bars}]{Colors.END}")
                        except (ValueError, IndexError):
                            print(f"  {Colors.YELLOW}! Could not parse signal strength{Colors.END}")
                    elif 'State' in line:
                        row("State", line.split(':', 1)[1].strip())
            else:
                print(f"  {Colors.RED}✗ Could not read WiFi interface data{Colors.END}")
        else:
            # For Linux/MacOS
            print(f"  {Colors.YELLOW}! Full WiFi info is only available on Windows{Colors.END}\n")

            # Check connection
            result = subprocess.run(['ping', '-c', '4', '8.8.8.8'],
                                     capture_output=True, text=True)
            if result.returncode == 0:
                row("Internet connection", "Active", Colors.GREEN)
            else:
                row_fail("Internet connection", "No connection")

    except Exception as e:
        row_fail("Network statistics", str(e))


def check_ping():
    """Check ping to popular servers"""
    section_header("📡", "PING CHECK")

    test_hosts = {
        'Google DNS': '8.8.8.8',
        'Cloudflare DNS': '1.1.1.1',
        'Yandex': 'ya.ru'
    }

    for name, host in test_hosts.items():
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            result = subprocess.run(['ping', param, '4', host],
                                     capture_output=True, text=True, timeout=10)

            ping_value = None

            if result.returncode == 0:
                if platform.system().lower() == 'windows':
                    # Windows output line looks like:
                    # "Minimum = 1ms, Maximum = 3ms, Average = 2ms"
                    match = re.search(r'Average\s*=\s*([\d.]+)\s*ms', result.stdout)
                    if match:
                        ping_value = float(match.group(1))
                else:
                    # Linux/macOS output line looks like:
                    # "rtt min/avg/max/mdev = 0.020/0.035/0.050/0.010 ms"
                    match = re.search(r'=\s*[\d.]+/([\d.]+)/[\d.]+/[\d.]+', result.stdout)
                    if match:
                        ping_value = float(match.group(1))

            if ping_value is not None:
                if ping_value < 50:
                    color = Colors.GREEN
                elif ping_value < 100:
                    color = Colors.YELLOW
                else:
                    color = Colors.RED
                row(name, f"{ping_value:.1f} ms", color)
            else:
                row_fail(name)
        except Exception:
            row_fail(name)


def speed_test():
    """Internet speed test"""
    section_header("🚀", "INTERNET SPEED TEST")
    print(f"  {Colors.GRAY}This may take up to a minute...{Colors.END}\n")

    try:
        st = speedtest.Speedtest()
        st.get_best_server()

        print(f"  {Colors.CYAN}⏳ Testing download speed...{Colors.END}")
        download_speed = st.download() / 1_000_000  # Convert to Mbps

        print(f"  {Colors.CYAN}⏳ Testing upload speed...{Colors.END}")
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps

        ping = st.results.ping

        print()
        print_box([
            (f"Download speed  {download_speed:.2f} Mbps",
             f"{Colors.BOLD}Download speed{Colors.END}  {Colors.GREEN}{download_speed:.2f} Mbps{Colors.END}"),
            (f"Upload speed  {upload_speed:.2f} Mbps",
             f"{Colors.BOLD}Upload speed{Colors.END}  {Colors.GREEN}{upload_speed:.2f} Mbps{Colors.END}"),
            (f"Ping  {ping:.2f} ms",
             f"{Colors.BOLD}Ping{Colors.END}  {Colors.GREEN}{ping:.2f} ms{Colors.END}"),
        ], title="SPEED TEST RESULTS")
        print()

        # Speed rating
        if download_speed >= 50:
            print(f"  {Colors.GREEN}★ EXCELLENT — great for 4K streaming and online gaming{Colors.END}")
        elif download_speed >= 25:
            print(f"  {Colors.YELLOW}★ GOOD — great for HD streaming{Colors.END}")
        elif download_speed >= 10:
            print(f"  {Colors.YELLOW}★ OK — fine for web browsing and SD video{Colors.END}")
        else:
            print(f"  {Colors.RED}★ SLOW — may not be enough for comfortable use{Colors.END}")

    except Exception as e:
        print(f"  {Colors.RED}✗ Error during speed test: {e}{Colors.END}")
        print(f"  {Colors.YELLOW}! Check your internet connection{Colors.END}")


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------

def show_donate_menu():
    """Show donate and bio links with selection"""
    while True:
        clear_screen()
        print_banner()

        print_box([
            ("1. 💰 Donate (DonationAlerts)", f"{Colors.GREEN}1.{Colors.END} 💰 {Colors.CYAN}Donate (DonationAlerts){Colors.END}"),
            ("    donationalerts.com/r/vasilievivan", f"    {Colors.GRAY}donationalerts.com/r/vasilievivan{Colors.END}"),
            None,
            ("2. 🔗 Bio (Guns.lol)", f"{Colors.GREEN}2.{Colors.END} 🔗 {Colors.CYAN}Bio (Guns.lol){Colors.END}"),
            ("    guns.lol/itzlazzy", f"    {Colors.GRAY}guns.lol/itzlazzy{Colors.END}"),
            None,
            ("0. Return to main menu", f"{Colors.GREEN}0.{Colors.END} {Colors.RED}Return to main menu{Colors.END}"),
        ], title="SUPPORT THE DEVELOPER")
        print()

        choice = input(f"  {Colors.CYAN}Select link to open (0-2): {Colors.END}").strip()

        if choice == '1':
            print(f"\n  {Colors.GREEN}Opening DonationAlerts in browser...{Colors.END}")
            webbrowser.open('https://www.donationalerts.com/r/vasilievivan')
            print(f"  {Colors.GREEN}✓ Thank you for your support! ❤️{Colors.END}")
            time.sleep(2)

        elif choice == '2':
            print(f"\n  {Colors.GREEN}Opening Bio page in browser...{Colors.END}")
            webbrowser.open('https://guns.lol/itzlazzy')
            print(f"  {Colors.GREEN}✓ Opening Guns.lol profile...{Colors.END}")
            time.sleep(2)

        elif choice == '0':
            break

        else:
            print(f"  {Colors.RED}! Invalid choice. Try again.{Colors.END}")
            time.sleep(1)


def main_menu():
    """Main menu of the program"""
    menu_items = [
        ("1", "🌐", "Show IP and ISP information"),
        ("2", "📶", "Show WiFi statistics"),
        ("3", "📡", "Check ping"),
        ("4", "🚀", "Internet speed test"),
        ("5", "💖", "Support developer (donate/bio)"),
        ("0", "🚪", "Exit"),
    ]

    while True:
        clear_screen()
        print_banner()

        lines = []
        for num, icon, text in menu_items:
            plain = f"{num}. {icon} {text}"
            colored = f"{Colors.GREEN}{num}.{Colors.END} {icon} {text}"
            lines.append((plain, colored))

        print_box(lines, title="MAIN MENU")
        print()

        choice = input(f"  {Colors.CYAN}Select action (0-5): {Colors.END}").strip()

        if choice == '1':
            clear_screen()
            print_banner()
            get_ip_info()
            wait_for_enter()

        elif choice == '2':
            clear_screen()
            print_banner()
            get_network_stats()
            wait_for_enter()

        elif choice == '3':
            clear_screen()
            print_banner()
            check_ping()
            wait_for_enter()

        elif choice == '4':
            clear_screen()
            print_banner()
            speed_test()
            wait_for_enter()

        elif choice == '5':
            show_donate_menu()

        elif choice == '0':
            print(f"\n  {Colors.GREEN}Goodbye! Thanks for using WiFi Checker!{Colors.END}\n")
            time.sleep(1)
            sys.exit(0)

        else:
            print(f"  {Colors.RED}! Invalid choice. Try again.{Colors.END}")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.YELLOW}! Program interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n  {Colors.RED}! Critical error: {e}{Colors.END}")
        sys.exit(1)