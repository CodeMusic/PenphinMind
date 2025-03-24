import wifi
import subprocess
from typing import List, Dict

class WifiManager:
    def __init__(self):
        self.interface = "wlan0"
        self.current_network = None

    def scan_networks(self) -> List[Dict]:
        """
        Scan for available WiFi networks
        """
        try:
            cmd = ['iwlist', self.interface, 'scan']
            scan_output = subprocess.check_output(cmd).decode('utf-8')
            networks = []
            for line in scan_output.split('\n'):
                if "ESSID:" in line:
                    ssid = line.split('ESSID:"')[1].split('"')[0]
                    networks.append({"ssid": ssid})
            return networks
        except Exception as e:
            print(f"Error scanning networks: {e}")
            return []

    def connect_to_network(self, ssid: str, password: str) -> bool:
        """
        Connect to a specific WiFi network
        """
        try:
            cmd = [
                'nmcli', 'device', 'wifi', 'connect', ssid,
                'password', password
            ]
            subprocess.check_call(cmd)
            self.current_network = ssid
            return True
        except Exception as e:
            print(f"Error connecting to network: {e}")
            return False

    def disconnect(self):
        """
        Disconnect from current WiFi network
        """
        try:
            cmd = ['nmcli', 'device', 'disconnect', self.interface]
            subprocess.check_call(cmd)
            self.current_network = None
            return True
        except Exception as e:
            print(f"Error disconnecting: {e}")
            return False

    def get_current_network(self) -> str:
        """
        Get current connected network name
        """
        return self.current_network 