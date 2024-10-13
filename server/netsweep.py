from datenbank import Datenbank
from netzwerkscanner import Geraet, Networkscanner
from typing import List, Tuple
import threading
from geraet import Geraet
import utils

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

    def dokumentiere(self, netzwerk_id, gefundene_geraete):
        def finde_geraet(mac_adresse, geraete_liste):
            return next((geraet for geraet in geraete_liste if utils.compare_macs(geraet.mac, mac_adresse)), None)

        registrierte_geraete = self.db.select_devices(netzwerk_id)

        if isinstance(registrierte_geraete, List):
            for geraet in registrierte_geraete:
                geraet_online = finde_geraet(geraet.mac, gefundene_geraete)

                if geraet_online:
                    if self.verbose:
                        print(f"match: {geraet}")
                    geraet_online.id = geraet.id
                    sql_statement = f"""
                    UPDATE geraete
                    SET
                        ip = CASE WHEN '{geraet_online.ip}' != 'Unbekannt' THEN '{geraet_online.ip}' ELSE ip END,
                        mdns_name = CASE WHEN '{geraet_online.mdns_name}' != 'Unbekannt' THEN '{geraet_online.mdns_name}' ELSE mdns_name END,
                        dns_name = CASE WHEN '{geraet_online.dns_name}' != 'Unbekannt' THEN '{geraet_online.dns_name}' ELSE dns_name END,
                        vnc_status = {geraet_online.vnc_status},
                        online_status = 1
                    WHERE id = {geraet_online.id};
                    """
                else:
                    if self.verbose:
                        print(f"no match: {geraet}")
                    sql_statement = f"""
                    UPDATE geraete
                    SET
                        vnc_status = 0,
                        online_status = 0
                    WHERE id = {geraet.id};
                    """

                try:
                    self.db.commit_sql(sql_statement)
                except Exception as e:
                    print(f"Gerät {geraet_online if geraet_online else geraet} konnte nicht dokumentiert werden: {e}")


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

    def run(self, netzwerk_id):
        while True:
            basis_ip, subnetzmaske = self.ip_und_maske_ermitteln(netzwerk_id)
            if not basis_ip or not subnetzmaske:
                break
            verfuegbare_geraete = self.scanner.scan(basis_ip, subnetzmaske)
            self.dokumentiere(netzwerk_id, verfuegbare_geraete)
            self.callback()

if __name__ == "__main__":
    try:
        ns = NetSweep(1, None, 3, True)
    except:
        print(f"Beim Ausführen von NetSweep ist ein Fehler aufgetreten.")
