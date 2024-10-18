from datenbank import Datenbank
from netzwerkscanner import Geraet, Networkscanner
from typing import List, Tuple
import threading
from geraet import Geraet
import utils
import concurrent.futures


class NetSweep:

    def __init__(self, callback, attempts, verbose, max_threads):
        self.callback = callback
        self.attempts = attempts
        self.verbose = verbose
        self.max_threads = max_threads

        self.scanner = Networkscanner(self.attempts, self.verbose, self.max_threads)
        self.db = Datenbank(None)

    def sweep(self, netzwerk_id):
        netsweep_thread = threading.Thread(target=self.run, args=(netzwerk_id,))
        netsweep_thread.start()

    def run(self, netzwerk_id):
        def finde_geraet(mac_adresse, geraete_liste):
            return next((geraet for geraet in geraete_liste if utils.compare_macs(geraet.mac, mac_adresse)), None)

        while True:
            basis_ip, subnetzmaske = self.ip_und_maske_ermitteln(netzwerk_id)

            if not basis_ip or not subnetzmaske:
                break

            geraete_online = self.scanner.scan(basis_ip, subnetzmaske)

            geraete_db = self.db.select_devices(netzwerk_id)

            liste = []

            geraete_online_mac = [geraet.mac for geraet in geraete_online]

            for geraet in geraete_db:
                if geraet.mac in geraete_online_mac:
                    geraet_online = finde_geraet(geraet.mac, geraete_online)
                    geraet.ip = geraet_online.ip
                    geraet.dns_name = geraet_online.dns_name
                    geraet.mdns_name = geraet_online.mdns_name
                    geraet.vnc_status = geraet_online.vnc_status
                    geraet.online_status = True
                else:
                    geraet.ip = ''
                    geraet.dns_name = ''
                    geraet.mdns_name = ''
                    geraet.vnc_status = False
                    geraet.online_status = False
                liste.append(geraet)

            self.deepscan_speichern(liste)

            if self.callback:
                self.callback()

    def deepscan_speichern(self, geraete):

        # print(geraete)
        # quit()

        def deepscan(geraet):

            if geraet.ip:
                print(f"scanning {geraet.mac} for dns name")
                geraet.dns_name = self.scanner.get_dns_name(geraet.ip) or ''
                print(f"scanning {geraet.mac} for mdns name")
                geraet.mdns_name = self.scanner.get_mdns_name(geraet.ip) or ''
                print(f"scanning {geraet.mac} for vnc status")
                geraet.vnc_status = self.scanner.get_vnc_status(geraet.ip) or False

            # print(f"After deepscan: {geraet}")

            sql_statement = f"""
            UPDATE geraete
            SET
                ip = CASE WHEN '{geraet.ip}' != '' THEN '{geraet.ip}' ELSE ip END,
                mdns_name = CASE WHEN '{geraet.mdns_name}' != '' THEN '{geraet.mdns_name}' ELSE mdns_name END,
                dns_name = CASE WHEN '{geraet.dns_name}' != '' THEN '{geraet.dns_name}' ELSE dns_name END,
                vnc_status = {1 if geraet.vnc_status else 0},
                online_status = {1 if geraet.online_status else 0}
            WHERE id = {geraet.id};
                """

            try:
                self.db.commit_sql(sql_statement)
            except Exception as e:
                print(f"Gerät {geraet} konnte nicht dokumentiert werden: {e}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for geraet in geraete:
                executor.submit(deepscan, geraet)

    def ip_und_maske_ermitteln(self, netzwerk_id) -> Tuple:
        sql_statement = f"""
        SELECT basis_ip, subnetzmaske
        FROM netzwerke
        WHERE id = {netzwerk_id};
        """
        results = self.db.commit_sql(sql_statement)
        assert(results != None)
        if isinstance(results, List):
            try:
                return results[0][0], results[0][1]
            except:
                print(f"Die Netzwerk-ID '{netzwerk_id}' konnte nicht zugeordnet werden.")
                return (None, None)
        return (None, None)


if __name__ == "__main__":
    try:
        ns = NetSweep(1, None, 3, True)
    except:
        print(f"Beim Ausführen von NetSweep ist ein Fehler aufgetreten.")
