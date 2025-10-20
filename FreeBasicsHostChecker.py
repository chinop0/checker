#!/usr/bin/env python3
import socket
import ssl
import time
from colorama import Fore, Style, init


# Initialize colorama
init(autoreset=True)

# Proxy configuration
PROXY_HOST = "157.240.195.32"
PROXY_PORT = 8080

def generate_header(host):
    """Generate the CONNECT header with required fields"""
    return (
        f"CONNECT {host}:443 HTTP/1.1\r\n"
        f"Host: {host}:443\r\n"
        "User-Agent: FBAV/0.0\r\n"
        "Proxy-Connection: Keep-Alive\r\n"
        "X-Iorg-Bsid: facebook\r\n"
        "\r\n"
    )

def test_host(host):
    """Test a single host through the proxy"""
    try:
        # Create socket and connect to proxy
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        start_time = time.time()
        
        sock.connect((PROXY_HOST, PROXY_PORT))
        connect_time = time.time() - start_time
        
        # Generate and send header
        header = generate_header(host)
        sock.sendall(header.encode())
        
        # Get initial response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response:
                break
        
        # Check if connection was successful
        if b"200 Connection Established" in response:
            # Create SSL connection
            context = ssl.create_default_context()
            ssock = context.wrap_socket(sock, server_hostname=host)
            
            # Get server response
            full_response = response
            try:
                while True:
                    chunk = ssock.recv(4096)
                    if not chunk:
                        break
                    full_response += chunk
            except socket.timeout:
                pass
            
            ssock.close()
            return full_response.decode('utf-8', 'ignore'), connect_time, True
        else:
            sock.close()
            return response.decode('utf-8', 'ignore'), connect_time, False
    
    except Exception as e:
        return f"Error: {str(e)}", 0, False

def print_banner():
    """Print the application banner"""
    print(Fore.CYAN + r"""
    
  ▄████  ▒█████   ██▓    ▓█████▄ ▓█████  ███▄    █     ██░ ██  ███▄ ▄███▓▒███████▒
 ██▒ ▀█▒▒██▒  ██▒▓██▒    ▒██▀ ██▌▓█   ▀  ██ ▀█   █    ▓██░ ██▒▓██▒▀█▀ ██▒▒ ▒ ▒ ▄▀░
▒██░▄▄▄░▒██░  ██▒▒██░    ░██   █▌▒███   ▓██  ▀█ ██▒   ▒██▀▀██░▓██    ▓██░░ ▒ ▄▀▒░ 
░▓█  ██▓▒██   ██░▒██░    ░▓█▄   ▌▒▓█  ▄ ▓██▒  ▐▌██▒   ░▓█ ░██ ▒██    ▒██   ▄▀▒   ░
░▒▓███▀▒░ ████▓▒░░██████▒░▒████▓ ░▒████▒▒██░   ▓██░   ░▓█▒░██▓▒██▒   ░██▒▒███████▒
 ░▒   ▒ ░ ▒░▒░▒░ ░ ▒░▓  ░ ▒▒▓  ▒ ░░ ▒░ ░░ ▒░   ▒ ▒     ▒ ░░▒░▒░ ▒░   ░  ░░▒▒ ▓░▒░▒
  ░   ░   ░ ▒ ▒░ ░ ░ ▒  ░ ░ ▒  ▒  ░ ░  ░░ ░░   ░ ▒░    ▒ ░▒░ ░░  ░      ░░░▒ ▒ ░ ▒
░ ░   ░ ░ ░ ░ ▒    ░ ░    ░ ░  ░    ░      ░   ░ ░     ░  ░░ ░░      ░   ░ ░ ░ ░ ░
      ░     ░ ░      ░  ░   ░       ░  ░         ░     ░  ░  ░       ░     ░ ░    
                          ░                                              ░                                                                                                                                                                                                         
    """ + Style.RESET_ALL)
    print(Fore.YELLOW + "=" * 65)
    print(Fore.MAGENTA + "Proxy Tester".center(65))
    print(Fore.YELLOW + "=" * 65)
    print(Fore.CYAN + f"Using Proxy: {PROXY_HOST}:{PROXY_PORT}".center(65))
    print(Fore.YELLOW + "=" * 65 + Style.RESET_ALL)
    print()

def print_host_result(host, response, connect_time, success):
    """Print test result for a single host"""
    print(Fore.YELLOW + f"\n[{host}]" + Style.RESET_ALL)
    print(Fore.CYAN + "-" * 65 + Style.RESET_ALL)
    
    if success:
        print(Fore.GREEN + f"✓ Connection successful ({connect_time:.2f}s)" + Style.RESET_ALL)
        print(Fore.CYAN + "Server Response:" + Style.RESET_ALL)
        
        # Highlight important parts of the response
        colored_response = response
        for keyword in ["200", "OK", "Connected", "Established"]:
            if keyword in colored_response:
                colored_response = colored_response.replace(
                    keyword, 
                    Fore.GREEN + keyword + Style.RESET_ALL
                )
                
        for keyword in ["404", "500", "Error", "Failed", "Timeout"]:
            if keyword in colored_response:
                colored_response = colored_response.replace(
                    keyword, 
                    Fore.RED + keyword + Style.RESET_ALL
                )
                
        print(colored_response)
    else:
        print(Fore.RED + f"✗ Connection failed ({connect_time:.2f}s)" + Style.RESET_ALL)
        print(Fore.CYAN + "Response:" + Style.RESET_ALL)
        print(response)
    
    print(Fore.CYAN + "-" * 65 + Style.RESET_ALL)

def main():
    """Main application loop"""
    while True:
        print_banner()
        
        # Get user input
        print(Fore.CYAN + "Enter host(s) to test (comma separated):" + Style.RESET_ALL)
        print(Fore.YELLOW + "Examples: google.com, youtube.com, facebook.com" + Style.RESET_ALL)
        print(Fore.CYAN + "> " + Style.RESET_ALL, end="")
        input_str = input().strip()
        
        if not input_str:
            continue
            
        hosts = [host.strip() for host in input_str.split(",") if host.strip()]
        
        # Test each host
        for host in hosts:
            print(Fore.MAGENTA + f"\nTesting {host}..." + Style.RESET_ALL)
            response, connect_time, success = test_host(host)
            print_host_result(host, response, connect_time, success)
            time.sleep(1)  # Brief pause between tests
        
        # Ask to test again
        print(Fore.CYAN + "\nTest completed. Would you like to test again? (y/n)" + Style.RESET_ALL)
        print(Fore.CYAN + "> " + Style.RESET_ALL, end="")
        choice = input().strip().lower()
        
        if choice != 'y':
            print(Fore.MAGENTA + "\nThank you for using Proxy Tester!")
            break

if __name__ == "__main__":
    main()
