import psutil
from prettytable import PrettyTable

def list_background_applications():
    table = PrettyTable(['PID', 'Name', 'Status', 'CPU Usage (%)', 'Memory (MB)'])
    
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            status = proc.info['status']
            cpu = proc.cpu_percent(interval=0.1)  # percent CPU usage
            mem = proc.info['memory_info'].rss / (1024 * 1024)  # resident memory in MB
            
            table.add_row([pid, name, status, f"{cpu:.2f}", f"{mem:.2f}"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process has been closed or inaccessible
            continue
    
    print(table)

if __name__ == '__main__':
    list_background_applications()
