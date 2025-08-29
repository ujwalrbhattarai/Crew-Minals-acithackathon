import psutil
from prettytable import PrettyTable
import time

def list_background_applications():
    table = PrettyTable(['PID', 'Name', 'Status', 'CPU Usage (%)', 'Memory (MB)'])
    
    # First call to initialize cpu_percent stats
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    time.sleep(0.1)  # short delay for CPU measurement
    
    for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            status = proc.info['status']
            cpu = proc.cpu_percent(interval=None)  # get updated CPU %
            mem = proc.info['memory_info'].rss / (1024 * 1024)  # resident memory in MB
            
            table.add_row([pid, name, status, f"{cpu:.2f}", f"{mem:.2f}"])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, ValueError):
            continue
    
    print(table)

if __name__ == '__main__':
    list_background_applications()
