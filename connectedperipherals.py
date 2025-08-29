import time
import os
import psutil

try:
    import pyudev  # For USB device names (Linux only)
    has_pyudev = True
except ImportError:
    has_pyudev = False

try:
    import bluetooth  # pybluez library
    has_bluetooth = True
except ImportError:
    has_bluetooth = False


def get_connected_usb():
    """Get connected USB devices with names (Linux only with pyudev)."""
    devices = []
    if not has_pyudev:
        return devices

    context = pyudev.Context()
    for device in context.list_devices(subsystem='usb', DEVTYPE='usb_device'):
        vendor = device.get("ID_VENDOR", "UnknownVendor")
        model = device.get("ID_MODEL", "UnknownDevice")
        name = f"USB: {vendor} {model}"
        devices.append(name)
    return devices


def get_bluetooth_devices():
    """Get paired Bluetooth device names."""
    devices = []
    if not has_bluetooth:
        return devices

    try:
        nearby = bluetooth.discover_devices(lookup_names=True, duration=4)
        for addr, name in nearby:
            devices.append(f"Bluetooth: {name}")
    except Exception:
        pass
    return devices


def get_connected_peripherals():
    devices = []

    # Skip charger as requested in original requirements
    # battery = psutil.sensors_battery()
    # if battery and battery.power_plugged:
    #     devices.append("Charger")

    # Detect external network adapters (like USB Wi-Fi dongles)
    net_if = psutil.net_if_addrs()
    for iface in net_if:
        # Only detect additional/external network interfaces
        if any(external_indicator in iface.lower() for external_indicator in [
            'usb', 'wireless', 'bluetooth', 'mobile', 'hotspot', 'tether'
        ]) and not any(builtin in iface.lower() for builtin in [
            'loopback', 'pseudo', 'virtual'
        ]):
            devices.append(f"External Network ({iface})")

    # Detect ALL removable/external drives (more inclusive)
    partitions = psutil.disk_partitions(all=True)
    for p in partitions:
        if "removable" in p.opts or "cdrom" in p.opts:
            devices.append(f"External Drive ({p.device})")

    # Try to detect USB devices using a different approach for Windows
    try:
        import subprocess
        result = subprocess.run(['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                device = line.strip()
                if device and device not in [p.device for p in partitions]:
                    devices.append(f"USB Drive ({device})")
    except:
        pass

    # USB devices (only external ones) - more lenient filtering
    usb_devices = get_connected_usb()
    for usb_dev in usb_devices:
        # Only filter out obvious internal components
        if not any(internal in usb_dev.lower() for internal in [
            'root hub', 'host controller', 'generic usb hub'
        ]):
            devices.append(usb_dev)

    # Enhanced Bluetooth device detection - only currently connected devices
    try:
        # First check if Bluetooth is enabled
        result = subprocess.run([
            'powershell', '-Command', 
            'Get-Service -Name "bthserv" | Select-Object Status'
        ], capture_output=True, text=True, shell=True)
        
        bluetooth_service_running = False
        if result.returncode == 0 and "Running" in result.stdout:
            bluetooth_service_running = True
        
        # Only proceed if Bluetooth service is running
        if bluetooth_service_running:
            # ONLY detect actively connected AND IN-USE Bluetooth devices
            try:
                # Method 1: Check for devices that are both connected AND actively communicating
                result = subprocess.run([
                    'powershell', '-Command', 
                    'Get-PnpDevice | Where-Object { $_.Class -eq "Bluetooth" -and $_.Status -eq "OK" -and $_.Problem -eq 0 -and $_.ConfigManagerErrorCode -eq 0 -and $_.InstanceId -like "*DEV_*" } | ForEach-Object { Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName "DEVPKEY_Device_Connected" | Where-Object { $_.Data -eq $true } | ForEach-Object { (Get-PnpDevice -InstanceId $_.InstanceId).FriendlyName } }'
                ], capture_output=True, text=True, shell=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        device_name = line.strip()
                        if (device_name and 
                            device_name != "FriendlyName" and 
                            not any(exclude in device_name.lower() for exclude in [
                                'adapter', 'radio', 'generic', 'microsoft', 'intel', 'realtek', 'enumerator'
                            ])):
                            bt_device_name = f"Bluetooth Device: {device_name}"
                            if bt_device_name not in devices:
                                devices.append(bt_device_name)
                
                # Method 2: Double-check with netsh but only for truly "Connected" status
                result2 = subprocess.run([
                    'netsh', 'bluetooth', 'show', 'devices'
                ], capture_output=True, text=True, shell=True)
                
                if result2.returncode == 0:
                    lines = result2.stdout.split('\n')
                    for line in lines:
                        # Only add if the line contains "Connected" AND the device is actively used
                        if ("Connected" in line and 
                            not any(exclude in line.lower() for exclude in [
                                'adapter', 'radio', 'generic', 'microsoft', 'intel', 'realtek'
                            ])):
                            device_name = line.split("Connected")[0].strip()
                            if device_name and len(device_name) > 3:
                                # Additional check: verify this device is actually in use
                                check_result = subprocess.run([
                                    'powershell', '-Command', 
                                    f'Get-PnpDevice | Where-Object {{ $_.FriendlyName -like "*{device_name}*" -and $_.Status -eq "OK" -and $_.Problem -eq 0 }}'
                                ], capture_output=True, text=True, shell=True)
                                
                                if check_result.returncode == 0 and check_result.stdout.strip():
                                    bt_device_name = f"Bluetooth Device: {device_name}"
                                    if bt_device_name not in devices:
                                        devices.append(bt_device_name)
            except:
                pass
                
    except:
        pass

    # Remove the old Bluetooth detection that was too broad

    # Try to detect connected phones/tablets via USB debugging
    try:
        # Check for Android devices
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if 'device' in line:
                    devices.append("Android Device (USB)")
    except:
        pass

    # Try to detect additional USB devices using Windows DevCon or PowerShell
    try:
        # Use PowerShell to get USB devices
        result = subprocess.run([
            'powershell', '-Command', 
            'Get-WmiObject -Class Win32_USBControllerDevice | ForEach-Object { [wmi]($_.Dependent) } | Where-Object { $_.Name -notlike "*Hub*" -and $_.Name -notlike "*Controller*" } | Select-Object Name'
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[2:]:  # Skip headers
                device_name = line.strip()
                if device_name and device_name != "Name" and device_name != "----":
                    # Filter to only external-looking devices
                    if any(external in device_name.lower() for external in [
                        'mouse', 'keyboard', 'camera', 'audio', 'headset', 'microphone',
                        'storage', 'flash', 'drive', 'phone', 'tablet', 'gamepad'
                    ]):
                        devices.append(f"USB Device: {device_name}")
    except:
        pass

    return devices if devices else ["None"]


def monitor_peripherals(interval=5):
    print("🔍 External Device Monitor Only (Press Ctrl+C to exit)")
    print("Excludes: Internal components, built-in Wi-Fi, chargers")

    previous_devices = set()

    while True:
        devices = set(get_connected_peripherals())

        # Detect new peripherals (no violation counting)
        new_devices = devices - previous_devices
        removed_devices = previous_devices - devices

        # Clear screen for fresh dashboard
        os.system('cls' if os.name == 'nt' else 'clear')

        print("🔌 External Devices Connected:\n")
        
        if "None" in devices and len(devices) == 1:
            print("   ❌ No external devices detected")
        else:
            device_list = [d for d in devices if d != "None"]
            if not device_list:
                print("   ❌ No external devices detected")
            else:
                for d in device_list:
                    print(f"   ✅ {d}")

        # Show device changes without counting violations
        if new_devices:
            new_device_list = [d for d in new_devices if d != "None"]
            if new_device_list:
                print(f"\n� New device(s) connected: {len(new_device_list)}")

        if removed_devices:
            removed_device_list = [d for d in removed_devices if d != "None"]
            if removed_device_list:
                print(f"\n❌ Device(s) disconnected: {len(removed_device_list)}")

        print(f"\n📊 External Devices: {len([d for d in devices if d != 'None'])}")

        previous_devices = devices
        time.sleep(interval)


if __name__ == "__main__":
    monitor_peripherals()
