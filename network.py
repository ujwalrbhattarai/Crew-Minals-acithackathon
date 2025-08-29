import psutil
import time
import datetime

# How often to check (seconds)
INTERVAL = 1  

# Counters for packet violations (just like your face/eye violations)
packet_in_counter = 0
packet_out_counter = 0

# Track last values
old_stats = psutil.net_io_counters()

print("Monitoring network traffic (Ctrl+C to stop)...")

try:
    while True:
        time.sleep(INTERVAL)

        # Current stats
        new_stats = psutil.net_io_counters()

        # Calculate packet differences
        packets_sent = new_stats.packets_sent - old_stats.packets_sent
        packets_recv = new_stats.packets_recv - old_stats.packets_recv

        # Update counters
        if packets_sent > 0:
            packet_out_counter += packets_sent
        if packets_recv > 0:
            packet_in_counter += packets_recv

        # Display info
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] IN: {packets_recv} OUT: {packets_sent} "
              f"| Total IN: {packet_in_counter} OUT: {packet_out_counter}")

        # Save current stats for next loop
        old_stats = new_stats

except KeyboardInterrupt:
    print("\nStopped monitoring.")
    print(f"Total Packets Received: {packet_in_counter}")
    print(f"Total Packets Sent: {packet_out_counter}")
