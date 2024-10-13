import os
import sqlite3
from datenbank import Datenbank
from utils import is_valid_ipv4, is_valid_subnet_mask, is_valid_mac, is_valid_checklist
import json

class ServerTools:
    def __init__(self):
        self.db = Datenbank()

    def commit_sql(self, statement):
        return self.db.commit_sql(statement)

    def wizzard(self, command):

        avatar = '🥷'

        def say(msg):
            border = "-" * len(msg)
            print(f"\n{avatar}\n{border}\n{msg}\n{border}\n")

        def ask(question: str):
            arr = question.split('\n')
            laengster_string = max(arr, key=len)
            border = "-" * len(laengster_string.strip())
            return input(f"\n{avatar}\n{border}\n" + "\n".join(arr) + f"\n{border}\n> ")

        def insert_network():
            name = ask("Wie ist der Name des Netzwerkes?")

            basis_ip = ask("Wie lautet seine Basis-IP?")
            if not is_valid_ipv4(basis_ip):
                say(f"⛔️ Die Basis-IP {basis_ip} ist ungültig!")
                return

            subnetzmaske = ask("Wie lautet die Subnetzmaske?")
            if not is_valid_subnet_mask(subnetzmaske):
                say(f"⛔️ Die Subnetzmaske {subnetzmaske} ist ungültig!")
                return

            self.db.insert_network(basis_ip, subnetzmaske, name)

            say(f"✅ Netzwerk erstellt.")

        def choose_network():
            networks = self.db.select_netzwerke()

            networks_list = ["Wähle:"]
            if isinstance(networks, list) and networks:
                for i, network in enumerate(networks):
                    network_id = networks[i][3]
                    network_name = networks[i][2]
                    network_ip = networks[i][0]
                    networks_list.append(f"{network_id} - {network_name}, {network_ip}")

            choice = ask('\n'.join(networks_list))

            return choice

        def insert_device(network_id):
            mac = ask("Wie lautet die MAC-Adresse des Geräts?")

            if not is_valid_mac:
                say(f"🚫 {mac} ist keine gültige MAC-Adresse")
                return

            device_id = self.db.insert_device(mac)
            if isinstance(device_id, int):
                self.db.insert_netzwerkteilnahme(network_id, device_id)
                say(f"✅ Gerät hinzugefügt.")

        def distribute_checklist(network_id):

            def read_json_file(file_path):
                try:
                    with open(file_path, 'r') as file:
                        data = json.load(file)
                    return data
                except FileNotFoundError:
                    print(f"Die Datei {file_path} wurde nicht gefunden.")
                    return None
                except json.JSONDecodeError:
                    print(f"Die Datei {file_path} enthält kein gültiges JSON.")
                    return None

            text = "Wie ist der Pfad zur Checkliste?"

            file_path = ask(text)

            json_data = read_json_file(file_path)

            valid, error = is_valid_checklist(json_data)

            if not valid:
                print(f"Fehler: {error}")
                return

            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:
                self.db.insert_checkliste(json.dumps(json_data), device.id)
                say(f"✅ Checklist zu {device.mac} hinzugefügt.")

        def add_credentials_network(network_id):
            user = ask("Nutzername?")
            password = ask("Passwort?")
            correct = ask(f"Nutzer: {user}\nPasswort: {password}\n\nRichtig? (j/n)")

            if not correct in ['j', 'y', 'ja', 'yes']:
                return

            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:
                user_id = self.db.insert_benutzer(user, password)

                assert(isinstance(user_id, int))

                self.db.insert_anmeldung(device.id, user_id)
                say(f"✅ Nutzer '{user}' für {device.mac} hinterlegt.")

        def remove_credentials_network(network_id):
            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:

                sql = f"""
                SELECT benutzer_id FROM anmeldungen
                WHERE geraet_id = {device.id};
                """

                row_user_ids = self.commit_sql(sql)

                sql = f"""
                DELETE FROM anmeldungen
                WHERE geraet_id = {device.id};
                """

                self.commit_sql(sql)

                assert(isinstance(row_user_ids, list))
                assert(row_user_ids)

                for user_id in row_user_ids:

                    user_id = user_id[0]

                    sql = f"""
                    DELETE FROM benutzer
                    WHERE id = {user_id};
                    """

                    self.commit_sql(sql)

                    say(f"✅ Nutzer '{user_id}' für {device.mac} entfernt.")

        def remove_checklists_network(network_id):

            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:
                sql = f"""
                DELETE FROM checklisten
                WHERE geraet_id = {device.id};
                """

                self.commit_sql(sql)
                say(f"✅ Checklisten gelöscht für Geraet {device.mac}.")

        def choose_device(network_id: int) -> int:
            row_devices = self.db.select_devices(network_id)

            assert(isinstance(row_devices, list))
            assert(row_devices)

            liste = list()
            for device in row_devices:
                liste.append(f"{device.id} - {device.mac}, {device.mdns_name}, {device.dns_name}")

            choice = int(ask("Wähle:\n" + '\n'.join(liste)))

            return choice

        def remove_device(device_id: int):
            sql = f"""
            DELETE FROM geraete
            WHERE id = {device_id};
            """

            self.commit_sql(sql)
            say(f"✅ Geraet {device_id} gelöscht.")

        def edit_network(network_id):
            text = "1 - Gerät hinzufügen\n"\
            "2 - Checkliste auslegen (für alle Geraete im Netz)\n"\
            "3 - Credentials hinterlegen (für alle Geraete im Netz)\n"\
            "4 - Credentials löschen (für alle Geraete im Netz)\n"\
            "5 - Checklisten löschen (für alle Geraete im Netz)\n"\
            "6 - Geraet entfernen"

            choice = ask(text)

            match choice:
                case '1':
                    insert_device(network_id)
                case '2':
                    distribute_checklist(network_id)
                case '3':
                    add_credentials_network(network_id)
                case '4':
                    remove_credentials_network(network_id)
                case '5':
                    remove_checklists_network(network_id)
                case '6':
                    remove_device(choose_device(network_id))

        def show_menu():
            text = "1 - Server starten\n"\
            "2 - Netzwerk hinzufügen\n"\
            "3 - Netzwerk bearbeiten"

            choice = ask(text)

            match choice:
                case '1':
                    from server import Server
                    network_id = choose_network()
                    Server('0.0.0.0', 5000, network_id, 5, False, 100).start()
                case '2':
                    insert_network()
                case '3':
                    network_id = choose_network()
                    while True:
                        edit_network(network_id)

        match command:
            case "insert network":
                insert_network()
            case "show menu":
                show_menu()

    def setup_database(self):

        def create_db(db_filename):
            sqlite3.connect(db_filename)
            create_table_statements = [
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
            for statement in create_table_statements:
                self.commit_sql(statement)

        def network_exists():
            result = self.commit_sql("SELECT COUNT(*) FROM netzwerke;")
            if isinstance(result, list) and result:
                return  result[0][0] > 0

        if not os.path.exists("netsweep.db"):
            create_db("netsweep.db")

        if not network_exists():
            self.wizzard("insert network")
            self.setup_database()

    def show_menu(self):
        self.wizzard("show menu")

#python3.11 -m nuitka --standalone --onefile --follow-imports server.py
