from utils import normalize_mac_address

class Geraet:

    def __init__(self, mac: str, ip: str, mdns_name: str, dns_name: str, vnc_status: bool, online_status: bool, benutzer: str, passwort: str, id: int):
        self.mac = normalize_mac_address(mac)
        self.ip = ip
        self.mdns_name = mdns_name
        self.dns_name = dns_name
        self.vnc_status = vnc_status
        self.online_status = online_status
        self.benutzer = benutzer
        self.passwort = passwort
        self.id = id

    def __repr__(self):
        return (f"Geraet(mac='{self.mac}', ip='{self.ip}', mdns_name='{self.mdns_name}', "
            f"dns_name='{self.dns_name}', vnc_status={self.vnc_status}, "
            f"online_status={self.online_status}, benutzer='{self.benutzer}', passwort='*****', "
            f"id={self.id})")
