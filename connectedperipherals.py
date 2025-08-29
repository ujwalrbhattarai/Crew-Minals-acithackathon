import time
import os
import psutil
import subprocess

try:
    import pyudev  # For Linux USB detection
    has_pyudev = True
except ImportError:
    has_pyudev = False


def get_connected_usb():
    """Get connected USB devices (Linux only with pyudev)."""
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


def get_connected_bluetooth():
    """Return only currently connected Bluetooth devices (Windows only)."""
    devices = []
    try:
        cmd = (
            'Get-PnpDevice | '
            'Where-Object { $_.Class -eq "Bluetooth" -and $_.Status -eq "OK" } | '
            'ForEach-Object { '
            ' $conn = Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName "DEVPKEY_Device_Connected"; '
            ' if ($conn.Data -eq $true) { $_.FriendlyName } '
            '}'
        )

        result = subprocess.run(['powershell', '-Command', cmd],
                                capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                name = line.strip()
                if name:
                    devices.append(f"Bluetooth Device: {name}")

    except Exception as e:
        pass

    return devices


def get_connected_peripherals():
    devices = []

    # Detect external network adapters
    for iface in psutil.net_if_addrs():
        if any(ext in iface.lower() for ext in ['usb', 'wireless', 'bluetooth', 'mobile', 'hotspot', 'tether']) and \
           not any(builtin in iface.lower() for builtin in ['loopback', 'pseudo', 'virtual']):
            devices.append(f"External Network ({iface})")

    # Detect external drives
    for p in psutil.disk_partitions(all=True):
        if "removable" in p.opts or "cdrom" in p.opts:
            devices.append(f"External Drive ({p.device})")

    # Detect USB drives using WMIC (Windows)
    try:
        result = subprocess.run(['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid'], 
                                capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n')[1:]:
                device = line.strip()
                if device:
                    devices.append(f"USB Drive ({device})")
    except:
        pass

    # Linux USB detection (optional)
    usb_devices = get_connected_usb()
    for usb_dev in usb_devices:
        if not any(internal in usb_dev.lower() for internal in ['root hub', 'host controller', 'generic usb hub']):
            devices.append(usb_dev)

    # Detect connected phones/tablets via ADB
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n')[1:]:
                if 'device' in line:
                    devices.append("Android Device (USB)")
    except:
        pass

    # Detect USB devices via PowerShell
    try:
        result = subprocess.run([
            'powershell', '-Command',
            'Get-WmiObject -Class Win32_USBControllerDevice | ForEach-Object { [wmi]($_.Dependent) } | '
            'Where-Object { $_.Name -notlike "*Hub*" -and $_.Name -notlike "*Controller*" } | Select-Object Name'
        ], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n')[2:]:
                name = line.strip()
                if name and name not in ["Name", "----"]:
                    if any(ext in name.lower() for ext in ['mouse', 'keyboard', 'camera', 'audio', 'headset',
                                                          'microphone', 'storage', 'flash', 'drive', 'phone', 'tablet', 'gamepad']):
                        devices.append(f"USB Device: {name}")
    except:
        pass

    # === Bluetooth: only currently connected devices ===
    devices += get_connected_bluetooth()

    return devices if devices else ["None"]


def monitor_peripherals(interval=5):
    print("🔍 External Device Monitor Only (Press Ctrl+C to exit)")
    print("Excludes: Internal components, built-in Wi-Fi, chargers")

    previous_devices = set()

    while True:
        devices = set(get_connected_peripherals())

        new_devices = devices - previous_devices
        removed_devices = previous_devices - devices

        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

        print("🔌 External Devices Connected:\n")
        if "None" in devices and len(devices) == 1:
            print("   ❌ No external devices detected")
        else:
            for d in [d for d in devices if d != "None"]:
                print(f"   ✅ {d}")

        if new_devices:
            print(f"\n🆕 New device(s) connected: {len(new_devices)}")
        if removed_devices:
            print(f"\n❌ Device(s) disconnected: {len(removed_devices)}")

        print(f"\n📊 External Devices: {len([d for d in devices if d != 'None'])}")

        previous_devices = devices
        time.sleep(interval)


if __name__ == "__main__":
    monitor_peripherals()
