from typing import List, Optional
import ipaddress
import threading
import os
import subprocess
import socket
from geraet import Geraet
import concurrent.futures
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Networkscanner:

    def __init__(self, attempts, verbose, max_threads, vnc_timeout=2):
        self.attempts = attempts
        self.verbose = verbose
        self.max_threads = max_threads
        self.vnc_timeout = vnc_timeout

    def info(self, msg):
        if not self.verbose:
            return
        logging.info(msg)

    def get_vnc_status(self, ip: str):
        """Überprüft, ob ein VNC-Server auf dem Standardport 5900 erreichbar ist."""
        self.info(f"ermittle VNC-Status von {ip}")
        vnc_port = 5900
        try:
            with socket.create_connection((str(ip), vnc_port), timeout=self.vnc_timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def get_mdns_name(self, ip: str):
        """Ermittelt den mDNS-Namen einer IP-Adresse."""
        self.info(f"ermittle mDNS-Name von {ip}")
        try:
            command = ['dig', '+short', '-x', str(ip), '@224.0.0.251', '-p', '5353']
            result = subprocess.check_output(command).decode().strip()
            return result if result else None
        except subprocess.CalledProcessError:
            return None

    def get_mac_address(self, ip: str):
        """Ermittelt die MAC-Adresse eines Hosts basierend auf der IP-Adresse."""
        self.info(f"ermittle MAC-Adresse von {ip}")
        try:
            if os.name != 'nt':
                command = ['arp', '-n', str(ip)]
                result = subprocess.check_output(command).decode()
                mac_address = result.split()[3]
            else:
                command = f'arp -a {ip}'
                result = subprocess.check_output(command, shell=True).decode()
                mac_address = result.split()[1]
            return mac_address
        except Exception as e:
            return None

    def get_hostname(self, ip: str):
        """Ermittelt den Hostnamen zu einer IP-Adresse."""
        self.info(f"ermittle Hostname von {ip}")
        try:
            hostname = socket.gethostbyaddr(str(ip))[0]
        except (socket.herror, socket.gaierror):
            hostname = None
        return hostname

    def ping_ip(self, ip: str):
        """Pingt eine IP-Adresse, um zu prüfen, ob das Gerät erreichbar ist."""
        success = False
        for i in range(self.attempts):
            # self.print(f"pinge ip: {ip} ({i + 1}. Versuch)")

            if os.name == 'nt':  # Windows
                command = ['ping', '-n', '1', '-w', '1000', str(ip)]  # 1000ms Timeout
            else:  # Unix/Linux/MacOS
                command = ['ping', '-c', '1', '-W', '1', str(ip)]  # 1s Timeout

            try:
                output = subprocess.check_output(command, stderr=subprocess.STDOUT)
                success = True
                break  # Wenn ein Ping erfolgreich ist, brich die Schleife ab
            except subprocess.CalledProcessError:
                continue  # Versuche es erneut

        return success

    def scan_ip(self, ip: str, results: List[Geraet]):
        """Scannt eine einzelne IP-Adresse und gibt die Informationen in die Ergebnisliste zurück."""
        if self.ping_ip(ip):
            self.info(f"Device found: {ip}")
            hostname = self.get_hostname(ip)
            mac_address = self.get_mac_address(ip)
            mdns_name = self.get_mdns_name(ip)
            vnc_reachable = self.get_vnc_status(ip)

            if mac_address:

                results.append(
                    Geraet(
                        mac_address,
                        str(ip),
                        mdns_name if mdns_name else 'Unbekannt',
                        hostname if hostname else 'Unbekannt',
                        True if vnc_reachable else False,
                        True,
                        "",
                        "",
                        -1
                    )
                )

    def get_network_range(self, ip: str, subnetzmaske: str):
        """Berechnet den IP-Bereich des Netzwerks basierend auf IP und Netzmaske."""
        network = ipaddress.IPv4Network(f"{ip}/{subnetzmaske}", strict=False)
        return list(network.hosts())

    def scan(self, ip: str, subnetzmaske: str) -> List[Geraet]:
        network_range = self.get_network_range(ip, subnetzmaske)

        self.info(f"Manuelle IP-Adresse: {ip}, Netzmaske: {subnetzmaske}")
        self.info("Suche nach Geräten im Netzwerk...")

        print("scanne netzwerk")

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [executor.submit(self.scan_ip, next_ip, results) for next_ip in network_range]
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Warten auf alle Threads

        print(f"fertig gescannt. {len(results)} interfaces gefunden. Gescannte IP's: {len(network_range)}")

        return results

if __name__ == "__main__":
    test = Networkscanner(1, True)
    print(test.scan("192.168.89.0","255.255.255.0"))
