from typing import List, Optional
import ipaddress
import threading
import os
import subprocess
import socket
from geraet import Geraet
import concurrent.futures
import logging
from utils import normalize_mac_address

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


    def get_vnc_status(self, ip: str) -> bool:
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


    def get_normalized_mac(self, ip: str):
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
            return normalize_mac_address(mac_address)
        except Exception as e:
            return None


    def get_dns_name(self, ip: str):
        """Ermittelt des dns-namen zu einer IP-Adresse."""
        self.info(f"ermittle dns-name von {ip}")
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


    def scan_ip(self, ip: str, results: list, target_macs: list):
        """Scan a single IP address and add the information to the results list."""
        if self.ping_ip(ip):
            self.info(f"Device found: {ip}")
            mac = self.get_normalized_mac(ip)
            dns_name = ''
            mdns_name = ''
            vnc_status = False

            if not target_macs or (target_macs and mac in target_macs):
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                    # Submit the tasks to the executor
                    dns_future = executor.submit(self.get_dns_name, ip)
                    mdns_future = executor.submit(self.get_mdns_name, ip)
                    vnc_future = executor.submit(self.get_vnc_status, ip)

                    # Get the results
                    dns_name = dns_future.result() or ''
                    mdns_name = mdns_future.result() or ''
                    vnc_status = vnc_future.result() or False

            if mac:
                # Add the result to the results list
                results.append(Geraet(mac, str(ip), mdns_name, dns_name, vnc_status, True, "", "", -1))


    def get_network_range(self, ip: str, subnetzmaske: str):
        """Berechnet den IP-Bereich des Netzwerks basierend auf IP und Netzmaske."""
        network = ipaddress.IPv4Network(f"{ip}/{subnetzmaske}", strict=False)
        return list(network.hosts())


    def scan(self, ip: str, subnetzmaske: str, target_macs: list) -> List[Geraet]:

        network_range = self.get_network_range(ip, subnetzmaske)

        self.info(f"Manuelle IP-Adresse: {ip}, Netzmaske: {subnetzmaske}")
        self.info("Suche nach Geräten im Netzwerk...")

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [executor.submit(self.scan_ip, next_ip, results, target_macs) for next_ip in network_range]
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Warten auf alle Threads

        return results
