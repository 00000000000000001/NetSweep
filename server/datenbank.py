import sqlite3
from typing import List, Union
from typing_extensions import Optional
from utils import normalize_mac_address
from geraet import Geraet
import os
import json

class Datenbank:
    filename = "netsweep.db"

    def __init__(self, callback=None, verbose=False):
        self.callback = callback
        self.verbose = verbose

    def create_sqlite_database(self):
        """ create a database connection to an SQLite database """
        conn = None
        try:
            conn = sqlite3.connect(self.filename)
            print("sqlite version: " + sqlite3.sqlite_version)
        except sqlite3.Error as e:
            print(e)
        finally:
            if conn:
                conn.close()

    def commit_sql(self, sql_statement) -> Union[List, int, None]:
        if self.verbose:
            print("Führe SQL-Statement aus: ")
            print(f'\033[32m{sql_statement.replace("  ", "").strip()}\033[0m')

        try:
            if not os.path.isfile(self.filename):
                with sqlite3.connect(self.filename) as conn:
                    cursor = conn.cursor()
                    # Hier können Sie den Code zum Erstellen der Datenbankstruktur hinzufügen
                    self.create_tables()
                    return self.commit_sql(sql_statement)
            else:
                with sqlite3.connect(self.filename) as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql_statement)
                    conn.commit()

                # Wenn es eine SELECT-Abfrage ist
                if sql_statement.strip().lower().startswith("select"):
                    rows = cursor.fetchall()
                    return rows

                # Wenn es eine INSERT-Abfrage ist
                elif sql_statement.strip().lower().startswith("insert"):
                    if self.callback:
                        self.callback()
                    return cursor.lastrowid

                # Für UPDATE und DELETE
                else:
                    if self.callback:
                        self.callback()
                    return None  # Keine speziellen Rückgabewerte

        except sqlite3.Error as e:
            print(f"SQL-Fehler: {e}")
            return None

    def drop_all_tables(self):

        sql_satements = [
            f"""
            DROP TABLE netzwerkteilnahmen;
            """,
            f"""
            DROP TABLE netzwerke;
            """,
            f"""
            DROP TABLE geraete;
            """,
            f"""
            DROP TABLE checklisten;
            """,
            f"""
            DROP TABLE benutzer;
            """,
            f"""
            DROP TABLE anmeldungen;
            """
        ]

        for statement in sql_satements:
            self.commit_sql(statement)

    def create_tables(self):
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS netzwerke (
           	basis_ip TEXT NOT NULL,
           	subnetzmaske TEXT NOT NULL,
           	name TEXT,
           	id INTEGER PRIMARY KEY AUTOINCREMENT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS geraete (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
           	mac TEXT UNIQUE,
           	ip TEXT,
           	mdns_name TEXT,
           	dns_name TEXT,
            vnc_status BOOLEAN CHECK (vnc_status IN (0, 1)),
            online_status BOOLEAN CHECK (online_status IN (0, 1))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS netzwerkteilnahmen (
           	netzwerk_id INTEGER NOT NULL,
           	geraet_id INTEGER NOT NULL,
           	FOREIGN KEY (netzwerk_id) REFERENCES netzwerke(id),
           	FOREIGN KEY (geraet_id) REFERENCES geraete(id),
           	PRIMARY KEY (netzwerk_id, geraet_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS checklisten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            geraet_id NOT NULL,
           	FOREIGN KEY (geraet_id) REFERENCES geraete(id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS benutzer (
           	id INTEGER PRIMARY KEY AUTOINCREMENT,
           	benutzer TEXT NOT NULL,
            passwort TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS anmeldungen (
            geraet_id INTEGER NOT NULL,
            benutzer_id INTEGER NOT NULL,
            FOREIGN KEY (geraet_id) REFERENCES geraete(id),
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
           	PRIMARY KEY (geraet_id, benutzer_id)
            );
            """
        ]
        for statement in sql_statements:
            self.commit_sql(statement)

    def insert_network(self, basis_ip, subnetzmaske, name):
        basis_ip = 'NULL' if basis_ip is None else f"'{basis_ip}'"
        subnetzmaske = 'NULL' if subnetzmaske is None else f"'{subnetzmaske}'"
        name = 'NULL' if name is None else f"'{name}'"

        sql = f"""
        INSERT INTO netzwerke (basis_ip, subnetzmaske, name) VALUES ({basis_ip}, {subnetzmaske}, {name});
        """

        res = self.commit_sql(sql)

        return res

    def insert_device(self, mac, ip=None, mdns_name=None, dns_name=None):

        mac = 'NULL' if mac is None else f"'{normalize_mac_address(mac)}'"
        ip = 'NULL' if ip is None else f"'{ip}'"
        mdns_name = 'NULL' if mdns_name is None else f"'{mdns_name}'"
        dns_name = 'NULL' if dns_name is None else f"'{dns_name}'"

        sql = f"""
        INSERT INTO geraete (mac, ip, mdns_name, dns_name) VALUES (UPPER({mac}), {ip}, {mdns_name}, {dns_name});
        """

        return self.commit_sql(sql)

    def insert_netzwerkteilnahme(self, netzwerk_id: int, geraet_id: int):
        # netzwerk_id = 'NULL' if netzwerk_id is None else f"{netzwerk_id}"
        # geraet_id = 'NULL' if geraet_id is None else f"{geraet_id}"

        sql = f"""
        INSERT INTO netzwerkteilnahmen (netzwerk_id, geraet_id) VALUES ({netzwerk_id}, {geraet_id});
        """

        return self.commit_sql(sql)

    def insert_checkliste(self, json_string: str, geraet_id: int):

        sql = f"""
        INSERT OR IGNORE INTO checklisten (data, geraet_id) VALUES ('{json_string}', {geraet_id});
        """
        return self.commit_sql(sql)

    def insert_aufgabe(self, name, erledigt, checkliste_id):

        name = 'NULL' if name is None else f"'{name}'"
        erledigt = 'NULL' if erledigt is None else f"{erledigt}"
        checkliste_id = 'NULL' if checkliste_id is None else f"{checkliste_id}"

        sql = f"""
        INSERT OR IGNORE INTO aufgaben (beschreibung, erledigt, checkliste_id) VALUES ({name}, {erledigt}, {checkliste_id});
        """
        return self.commit_sql(sql)

    def insert_benutzer(self, benutzer, passwort):

        benutzer = 'NULL' if benutzer is None else f"'{benutzer}'"
        passwort = 'NULL' if passwort is None else f"'{passwort}'"

        sql = f"""
        INSERT INTO benutzer (benutzer, passwort) VALUES ({benutzer}, {passwort});
        """
        return self.commit_sql(sql)

    def insert_anmeldung(self, geraet_id: int, nutzer_id: int):

        # geraet_id = 'NULL' if geraet_id is None else f"'{geraet_id}'"
        # nutzer_id = 'NULL' if nutzer_id is None else f"'{nutzer_id}'"

        sql = f"""
        INSERT INTO anmeldungen (geraet_id, benutzer_id) VALUES ({geraet_id}, {nutzer_id});
        """
        return self.commit_sql(sql)

    def select_user(self, geraet_id: int):
        sql = f"""SELECT * FROM benutzer AS a
        JOIN anmeldungen AS b
        ON a.id = b.benutzer_id
        WHERE b.geraet_id = {geraet_id};"""

        return self.commit_sql(sql)

    def select_netzwerke(self):
        sql = f"SELECT * FROM netzwerke;"

        return self.commit_sql(sql)

    def select_devices(self, netzwerk_id: int) -> List[Geraet]:

        sql = f"""
        SELECT a.mac, a.ip, a.mdns_name, a.dns_name,  a.vnc_status, a.online_status, d.benutzer, d.passwort, a.id
		FROM geraete AS a
        LEFT JOIN netzwerkteilnahmen AS b
		ON a.id = b.geraet_id
		LEFT JOIN anmeldungen AS c
        ON a.id = c.geraet_id
		LEFT JOIN benutzer AS d
		ON c.benutzer_id = d.id
        WHERE b.netzwerk_id = {netzwerk_id};
        """

        results = self.commit_sql(sql)

        geraete = []
        if isinstance(results, List):
            for r in results:
                geraete.append(Geraet(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]))

        return geraete

    def select_checklist(self, checklist_id: int):
        sql = f"""
        SELECT * FROM checklisten
        WHERE id = {checklist_id};
        """

        return self.commit_sql(sql)

    def select_checklists_by_device(self, device_id):
        sql = f"""
        SELECT * FROM checklisten
        WHERE geraet_id = {device_id};
        """

        return self.commit_sql(sql)

    def select_aufgaben(self, checkliste_id: int):
        sql = f"""
        SELECT * FROM aufgaben
        WHERE checkliste_id = {checkliste_id};
        """

        return self.commit_sql(sql)

    def delete_geraet(self, id):
        sql_statements = [
        f"""
        DELETE FROM netzwerkteilnahmen
        WHERE geraet_id = {id};
        """,
        f"""
        DELETE FROM geraete
        WHERE id = {id};
        """
        ]

        for statement in sql_statements:
            self.commit_sql(statement)

    def delete_checkliste(self, checkliste_id):
        sql = f"""
        DELETE FROM checklisten
        WHERE id = {checkliste_id};
        """

        self.commit_sql(sql)

    def delete_benutzer(self, benutzer_id):
        sql = f"""
        DELETE FROM benutzer
        WHERE id = {benutzer_id};
        """

        self.commit_sql(sql)

    def update_checklist(self, checklist_id: int, pfad: list, erledigt: bool):
        row = self.select_checklist(checklist_id)

        assert(isinstance(row, list))
        assert(row)

        json_str = row[0][1]
        json_data = json.loads(json_str)

        aufgabe = json_data
        for s in pfad:
            if isinstance(aufgabe, list):
                aufgabe = aufgabe[int(s)]
                break
            aufgabe = aufgabe[s]

        for key in aufgabe:
            aufgabe[key] = erledigt

        sql = f"""
        UPDATE checklisten
        SET data = '{json.dumps(json_data)}'
        WHERE id = {checklist_id};
        """

        self.commit_sql(sql)

if __name__ == '__main__':
    test = Datenbank()
    test.create_sqlite_database()
    test.create_tables()
