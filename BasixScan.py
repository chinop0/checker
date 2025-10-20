import socket
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# --- Default single proxy (kept for compatibility) ---
PROXY_IP = "157.240.195.32"
PROXY_PORT = 8080  # always use 8080 for "all proxies" scans as requested

# --- List of all proxies for "scan against all proxies" options ---
ALL_PROXIES = [
    "31.13.94.39","31.13.84.39","157.240.8.39","179.60.195.39","157.240.9.39",
    "157.240.234.38","157.240.222.32","31.13.85.39","157.240.226.38","157.240.12.39",
    "31.13.90.36","31.13.80.39","157.240.17.32","157.240.204.32","163.70.152.41",
    "57.144.114.4","157.240.30.39","185.60.217.39","157.240.27.39","57.144.248.4",
    "57.144.244.4","157.240.0.38","157.240.253.39","157.240.210.32","157.240.223.32",
    "157.240.200.32","102.132.97.39","102.132.103.36","157.240.243.39","31.13.83.39",
    "157.240.5.32","157.240.205.37","157.240.195.32","157.240.196.32","185.60.219.38",
    "157.240.202.37","163.70.128.38","57.144.238.4","57.144.240.4","163.70.151.38",
    "157.240.214.38","157.240.225.38","157.240.233.38","157.240.199.32","157.240.211.38",
    "57.144.100.4","157.240.208.32","31.13.95.38","31.13.73.38","157.240.23.37",
    "157.240.192.32","163.70.146.39","163.70.140.41","157.240.1.38","31.13.64.39",
    "157.240.16.38","157.240.242.39","163.70.144.33","157.240.237.39","57.144.124.4",
    "157.240.198.32","157.240.239.38","31.13.86.39","31.13.69.38","157.240.231.38",
    "157.240.209.32","31.13.82.39","31.13.76.32","157.240.215.32","157.240.244.39",
    "31.13.89.37","157.240.25.38","157.240.236.36","163.70.132.41","163.70.137.39",
    "102.132.101.38","57.144.222.4","157.240.201.32","31.13.78.37","157.240.227.38",
    "157.240.197.32","163.70.130.39","57.144.110.4","157.240.212.32","157.240.29.36",
    "185.60.218.39","31.13.72.39","57.144.152.4","57.144.14.4","57.144.160.4",
    "157.240.13.39","157.240.15.38","163.70.148.33","163.70.149.42","57.144.126.4",
    "31.13.87.39","157.240.224.39","31.13.66.32","157.240.229.38","57.144.22.4",
    "157.240.14.38","57.144.204.4","157.240.254.39","57.144.218.4","31.13.93.37",
    "57.144.104.4","157.240.24.37","57.144.252.4","31.13.88.38","31.13.70.39",
    "157.240.11.39","157.240.26.39","57.144.116.4","57.144.102.4","157.240.22.38",
    "157.240.3.39","31.13.71.39","157.240.241.38","157.240.245.39","102.132.99.38",
    "102.132.104.41"
]

# --- Colors ---
COLOR_200 = "\033[38;5;40m"
COLOR_403 = "\033[38;5;203m"
COLOR_429 = "\033[38;5;214m"
COLOR_502 = "\033[38;5;141m"
COLOR_OTHER = "\033[38;5;245m"
COLOR_TITLE = "\033[38;5;39m"
COLOR_MENU = "\033[38;5;45m"
COLOR_PROMPT = "\033[38;5;51m"
COLOR_STATUS = "\033[38;5;228m"
COLOR_HOST = "\033[38;5;117m"
COLOR_RESET = "\033[0m"
BOLD = "\033[1m"

MAX_WORKERS = 300
SOCKET_TIMEOUT = 30
RECV_BUFFER = 8192


def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    width = 54
    title = "FreeBasics Checker"
    developer = "Developed by: FirewallFalcon"
    print(f"{COLOR_TITLE}{BOLD}")
    print("+" + "-" * width + "+")
    print(f"|{title.center(width)}|")
    print(f"|{developer.center(width)}|")
    print("+" + "-" * width + "+")
    print(f"{COLOR_RESET}")


def send_custom_payload(proxy_ip, proxy_port, target_host, target_port=443):
    payload = (
        f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
        f"Host: {target_host}:{target_port}\r\n"
        f"Proxy-Connection: keep-alive\r\n"
        f"User-Agent: Mozilla/5.0 (Linux; Android 14; SM-A245F) "
        f"Chrome/133.0.6943.122 [FBAN/InternetOrgApp;FBAV/166.0.0.0.169;]\r\n"
        f"X-IORG-BSID: a08359b0-d7ec-4cb5-97bf-000bdc29ec87\r\n"
        f"X-IORG-SERVICE-ID: null\r\n\r\n"
    )
    try:
        with socket.create_connection((proxy_ip, proxy_port), timeout=SOCKET_TIMEOUT) as sock:
            sock.settimeout(SOCKET_TIMEOUT)
            sock.sendall(payload.encode())
            response = sock.recv(RECV_BUFFER).decode(errors="ignore")
            return response
    except Exception as e:
        return f"[ERROR] {str(e)}"


def categorize_response(response):
    if "200" in response:
        return "200 OK"
    elif "403" in response:
        return "403 Forbidden"
    elif "429" in response:
        return "429 Too Many Requests"
    elif "502" in response:
        return "502 Bad Gateway"
    elif response.startswith("[ERROR]"):
        return "Others"
    else:
        return "Others"


def get_color(status):
    return {
        "200 OK": COLOR_200,
        "403 Forbidden": COLOR_403,
        "429 Too Many Requests": COLOR_429,
        "502 Bad Gateway": COLOR_502
    }.get(status, COLOR_OTHER)


def print_summary(summary):
    max_len = max(len(k) for k in summary.keys())
    print(f"\n{COLOR_STATUS}{BOLD}SUMMARY:{COLOR_RESET}")
    for status, count in summary.items():
        print(f"  {get_color(status)}{status:<{max_len}}{COLOR_RESET} : {count}")


def load_hosts_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{COLOR_403}File not found: {file_path}{COLOR_RESET}")
        return []


def load_hosts_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return [line.strip() for line in resp.text.splitlines() if line.strip()]
        else:
            print(f"{COLOR_403}Failed to fetch URL (status {resp.status_code}){COLOR_RESET}")
            return []
    except Exception as e:
        print(f"{COLOR_403}Error fetching URL: {e}{COLOR_RESET}")
        return []


def scan_multiple_hosts(proxy_ip, proxy_port, hosts):
    results = []
    summary = {"200 OK": 0, "403 Forbidden": 0, "429 Too Many Requests": 0, "502 Bad Gateway": 0, "Others": 0}

    hosts_200, hosts_403, hosts_429, hosts_502, hosts_others = [], [], [], [], []

    print(f"\n{BOLD}Scanning {len(hosts)} hosts...{COLOR_RESET}\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_host = {executor.submit(send_custom_payload, proxy_ip, proxy_port, h): h for h in hosts}
        for i, future in enumerate(as_completed(future_to_host), 1):
            host = future_to_host[future]
            try:
                response = future.result()
            except Exception as e:
                response = f"[ERROR] {e}"
            status = categorize_response(response)
            summary[status] += 1

            if status == "200 OK":
                hosts_200.append(host)
            elif status == "403 Forbidden":
                hosts_403.append(host)
            elif status == "429 Too Many Requests":
                hosts_429.append(host)
            elif status == "502 Bad Gateway":
                hosts_502.append(host)
            else:
                hosts_others.append(host)

            print(f"{COLOR_HOST}[{i}/{len(hosts)}] Checking: {host}{COLOR_RESET}")
            print(f"  {COLOR_STATUS}Status:{COLOR_RESET} {get_color(status)}{status}{COLOR_RESET}")
            print_summary(summary)
            print(f"{COLOR_OTHER}{'─'*60}{COLOR_RESET}")
            results.append(f"{status} → {host}\n{response}\n{'═'*50}")

    groups_ordered = [
        ("200 OK hosts", hosts_200),
        ("429 Too Many Requests hosts", hosts_429),
        ("502 Bad Gateway hosts", hosts_502),
        ("Others hosts", hosts_others),
        ("403 Forbidden hosts", hosts_403),
    ]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"hosts_grouped_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for group_name, group_hosts in groups_ordered:
            f.write(group_name + "\n")
            if group_hosts:
                for h in group_hosts:
                    f.write(h + "\n")
            else:
                f.write("(None)\n")
            f.write("\n")

    print(f"{COLOR_200}Saved grouped hosts to {filename}{COLOR_RESET}")

    with open(f"scan_results_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))


def scan_single_host(proxy_ip, proxy_port, host):
    print(f"\n{COLOR_HOST}Checking: {host}{COLOR_RESET}")
    response = send_custom_payload(proxy_ip, proxy_port, host)
    status = categorize_response(response)
    print(f"\n{COLOR_STATUS}Status:{COLOR_RESET} {get_color(status)}{status}{COLOR_RESET}")
    print(f"{BOLD}Response:{COLOR_RESET}\n{response}")
    print(f"{COLOR_OTHER}{'─'*30}{COLOR_RESET}")


def scan_host_against_all_proxies(host):
    """
    Scan a single target host through every proxy in ALL_PROXIES (port 8080).
    Save grouped results in one file and save full raw responses to another file.
    """
    results = []
    grouped = {"200 OK": [], "403 Forbidden": [], "429 Too Many Requests": [], "502 Bad Gateway": [], "Others": []}
    summary = {k: 0 for k in grouped.keys()}

    print(f"\n{BOLD}Scanning host '{host}' through {len(ALL_PROXIES)} proxies (port 8080)...{COLOR_RESET}\n")

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(ALL_PROXIES))) as executor:
        future_to_proxy = {executor.submit(send_custom_payload, proxy_ip, 8080, host): proxy_ip for proxy_ip in ALL_PROXIES}
        for i, future in enumerate(as_completed(future_to_proxy), 1):
            proxy_ip = future_to_proxy[future]
            try:
                response = future.result()
            except Exception as e:
                response = f"[ERROR] {e}"

            status = categorize_response(response)
            summary[status] += 1
            grouped[status].append(proxy_ip)

            print(f"{COLOR_HOST}[{i}/{len(ALL_PROXIES)}] Proxy: {proxy_ip}{COLOR_RESET}")
            print(f"  {COLOR_STATUS}Status:{COLOR_RESET} {get_color(status)}{status}{COLOR_RESET}")
            print_summary(summary)
            print(f"{COLOR_OTHER}{'─'*60}{COLOR_RESET}")

            results.append(f"{proxy_ip} → {status}\n{response}\n{'═'*50}")

    # Save grouped and raw results (single grouped file contains grouped lists and raw responses appended)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    grouped_filename = f"proxy_scan_grouped_{host}_{timestamp}.txt"
    raw_filename = f"proxy_scan_raw_{host}_{timestamp}.txt"

    with open(grouped_filename, "w", encoding="utf-8") as f:
        f.write(f"Scan target: {host}\n")
        f.write(f"Scanned at: {datetime.now().isoformat()}\n\n")
        for key in ["200 OK", "429 Too Many Requests", "502 Bad Gateway", "403 Forbidden", "Others"]:
            f.write(f"{key} ({len(grouped[key])}):\n")
            if grouped[key]:
                for p in grouped[key]:
                    f.write(f"  {p}\n")
            else:
                f.write("  (None)\n")
            f.write("\n")
        f.write("\n=== Raw responses below ===\n\n")
        for r in results:
            f.write(r + "\n")

    # Also save raw-only file for convenience
    with open(raw_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"{COLOR_200}Saved grouped results to {grouped_filename}{COLOR_RESET}")
    print(f"{COLOR_200}Saved raw results to {raw_filename}{COLOR_RESET}")


def scan_multiple_hosts_against_all_proxies(hosts):
    """
    For each host in hosts, scan through ALL_PROXIES (port 8080).
    Save one grouped file that contains grouped proxy lists per host, and one raw file.
    Hosts are processed sequentially to limit resource explosion; proxies scanned in parallel per host.
    """
    all_results_raw = []
    all_grouped_summary = {}  # host -> grouped dict

    print(f"\n{BOLD}Scanning {len(hosts)} hosts through {len(ALL_PROXIES)} proxies each (port 8080)...{COLOR_RESET}\n")

    for idx, host in enumerate(hosts, 1):
        print(f"{COLOR_TITLE}{BOLD}Host [{idx}/{len(hosts)}]: {host}{COLOR_RESET}")
        # reuse scan_host_against_all_proxies logic but capture structures rather than writing files per-host
        results = []
        grouped = {"200 OK": [], "403 Forbidden": [], "429 Too Many Requests": [], "502 Bad Gateway": [], "Others": []}
        summary = {k: 0 for k in grouped.keys()}

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(ALL_PROXIES))) as executor:
            future_to_proxy = {executor.submit(send_custom_payload, proxy_ip, 8080, host): proxy_ip for proxy_ip in ALL_PROXIES}
            for i, future in enumerate(as_completed(future_to_proxy), 1):
                proxy_ip = future_to_proxy[future]
                try:
                    response = future.result()
                except Exception as e:
                    response = f"[ERROR] {e}"

                status = categorize_response(response)
                summary[status] += 1
                grouped[status].append(proxy_ip)

                print(f"{COLOR_HOST}[{i}/{len(ALL_PROXIES)}] Proxy: {proxy_ip}{COLOR_RESET}")
                print(f"  {COLOR_STATUS}Status:{COLOR_RESET} {get_color(status)}{status}{COLOR_RESET}")
                print_summary(summary)
                print(f"{COLOR_OTHER}{'─'*60}{COLOR_RESET}")

                results.append(f"{proxy_ip} → {status}\n{response}\n{'═'*50}")

        all_results_raw.append((host, results))
        all_grouped_summary[host] = grouped

    # Save one grouped file containing grouped lists per host + appended raw responses
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    grouped_filename = f"multi_hosts_proxy_grouped_{timestamp}.txt"
    raw_filename = f"multi_hosts_proxy_raw_{timestamp}.txt"

    with open(grouped_filename, "w", encoding="utf-8") as f:
        f.write(f"Multi-host proxy scan grouped results\nScanned at: {datetime.now().isoformat()}\n\n")
        for host, grouped in all_grouped_summary.items():
            f.write(f"Host: {host}\n")
            for key in ["200 OK", "429 Too Many Requests", "502 Bad Gateway", "403 Forbidden", "Others"]:
                f.write(f"  {key} ({len(grouped[key])}):\n")
                if grouped[key]:
                    for p in grouped[key]:
                        f.write(f"    {p}\n")
                else:
                    f.write("    (None)\n")
                f.write("\n")
            f.write("\n" + ("-" * 60) + "\n\n")

        f.write("\n=== Raw responses by host below ===\n\n")
        for host, results in all_results_raw:
            f.write(f"=== Host: {host} ===\n")
            for r in results:
                f.write(r + "\n")
            f.write("\n\n")

    with open(raw_filename, "w", encoding="utf-8") as f:
        for host, results in all_results_raw:
            f.write(f"=== Host: {host} ===\n")
            f.write("\n".join(results))
            f.write("\n\n")

    print(f"{COLOR_200}Saved grouped multi-host results to {grouped_filename}{COLOR_RESET}")
    print(f"{COLOR_200}Saved raw multi-host results to {raw_filename}{COLOR_RESET}")


def main():
    print_banner()
    while True:
        print(f"\n{COLOR_TITLE}{BOLD}MAIN MENU:{COLOR_RESET}")
        print(f"  {COLOR_MENU}1.{COLOR_RESET} Single Host Check (use PROXY_IP/default single proxy)")
        print(f"  {COLOR_MENU}2.{COLOR_RESET} Multiple Host Check (manual input, uses PROXY_IP)")
        print(f"  {COLOR_MENU}3.{COLOR_RESET} Load hosts from file (uses PROXY_IP)")
        print(f"  {COLOR_MENU}4.{COLOR_RESET} Load hosts from URL (uses PROXY_IP)")
        print(f"  {COLOR_MENU}5.{COLOR_RESET} Scan single host through ALL proxies (port 8080, grouped file)")
        print(f"  {COLOR_MENU}6.{COLOR_RESET} Scan multiple hosts through ALL proxies (port 8080, grouped file)")
        print(f"  {COLOR_MENU}7.{COLOR_RESET} Exit")
        print(f"{COLOR_TITLE}{'─'*60}{COLOR_RESET}")

        choice = input(f"\n{COLOR_PROMPT}Select (1-7): {COLOR_RESET}").strip()

        if choice == "1":
            host = input(f"{COLOR_PROMPT}Enter host: {COLOR_RESET}").strip()
            if host:
                scan_single_host(PROXY_IP, PROXY_PORT, host)

        elif choice == "2":
            print(f"\n{COLOR_PROMPT}Enter hosts (one per line), 'done' to finish:{COLOR_RESET}")
            hosts = []
            while True:
                line = input().strip()
                if line.lower() == 'done':
                    break
                if line:
                    hosts.append(line)
            if hosts:
                scan_multiple_hosts(PROXY_IP, PROXY_PORT, hosts)

        elif choice == "3":
            file_path = input(f"{COLOR_PROMPT}Enter path to .txt file: {COLOR_RESET}").strip()
            hosts = load_hosts_from_file(file_path)
            if hosts:
                scan_multiple_hosts(PROXY_IP, PROXY_PORT, hosts)

        elif choice == "4":
            url = input(f"{COLOR_PROMPT}Enter URL (e.g. GitHub raw link): {COLOR_RESET}").strip()
            hosts = load_hosts_from_url(url)
            if hosts:
                scan_multiple_hosts(PROXY_IP, PROXY_PORT, hosts)

        elif choice == "5":
            host = input(f"{COLOR_PROMPT}Enter target host to test through all proxies: {COLOR_RESET}").strip()
            if host:
                scan_host_against_all_proxies(host)

        elif choice == "6":
            print(f"\n{COLOR_PROMPT}Enter hosts (one per line), 'done' to finish:{COLOR_RESET}")
            hosts = []
            while True:
                line = input().strip()
                if line.lower() == 'done':
                    break
                if line:
                    hosts.append(line)
            if not hosts:
                # ask if they want to load from file or URL
                sub = input(f"{COLOR_PROMPT}No manual hosts entered. Load from (f)ile or (u)rl? (f/u/skip): {COLOR_RESET}").strip().lower()
                if sub == 'f':
                    file_path = input(f"{COLOR_PROMPT}Enter path to .txt file: {COLOR_RESET}").strip()
                    hosts = load_hosts_from_file(file_path)
                elif sub == 'u':
                    url = input(f"{COLOR_PROMPT}Enter URL (e.g. GitHub raw link): {COLOR_RESET}").strip()
                    hosts = load_hosts_from_url(url)
                else:
                    print(f"{COLOR_403}No hosts provided. Returning to main menu.{COLOR_RESET}")
                    continue

            if hosts:
                scan_multiple_hosts_against_all_proxies(hosts)

        elif choice == "7":
            print(f"{COLOR_TITLE}Exiting...{COLOR_RESET}")
            break

        else:
            print(f"{COLOR_403}Invalid choice.{COLOR_RESET}")


if __name__ == "__main__":
    main()
