import socket
import psutil
import time
from datetime import datetime
from collections import defaultdict

def resolve_host(ip):
    """Resolve IP to hostname/domain"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        # Extract domain name (remove subdomains if needed)
        return hostname
    except (socket.herror, socket.gaierror):
        return ip

def get_active_connections():
    """Get active network connections using psutil"""
    connections = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'ESTABLISHED' and conn.raddr:
            connections.append({
                'remote_ip': conn.raddr.ip if hasattr(conn.raddr, 'ip') else conn.raddr[0],
                'remote_port': conn.raddr.port if hasattr(conn.raddr, 'port') else conn.raddr[1]
            })
    return connections

def monitor_network():
    """Monitor network connections and show time + domain names"""
    print("Network Activity Monitor - Time and Domains")
    print("=" * 50)
    
    seen_domains = set()
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            current_connections = get_active_connections()
            
            for conn in current_connections:
                remote_ip = conn['remote_ip']
                domain = resolve_host(remote_ip)
                
                # Only show new domains or refresh every 30 seconds
                domain_key = domain
                if domain_key not in seen_domains:
                    seen_domains.add(domain_key)
                    print(f"[{current_time}] {domain}")
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Network monitoring stopped.")

if __name__ == "__main__":
    monitor_network()