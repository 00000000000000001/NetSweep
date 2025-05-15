import os
import sqlite3
from datenbank import Datenbank
from utils import is_valid_ipv4, is_valid_subnet_mask, is_valid_mac, is_valid_checklist
import json
import time
import sys
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

class ServerTools:
    def __init__(self):
        self.db = Datenbank()

    def commit_sql(self, statement):
        return self.db.commit_sql(statement)

    def wizzard(self, command):

        # avatar = '🥷'

        def say(msg):
            border = "-" * len(msg)
            # print(f"\n{avatar}\n{border}")
            print()
            for char in msg:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(0.001)  # Verzögerung von 50 Millisekunden
            print(f"\n{border}\n")

        def ask(question: str):
            arr = question.split('\n')
            laengster_string = max(arr, key=len)
            border = "-" * len(laengster_string.strip())
            # print(f"\n{avatar}\n{border}")
            print()
            for line in arr:
                for char in line:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(0.001)  # Verzögerung von 50 Millisekunden
                sys.stdout.write("\n")  # Zeilenumbruch nach jeder Zeile
            print(border)
            return input("> ")

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

        def insert_geraet_by_mac(network_id, mac):
            if not is_valid_mac(mac):
                say(f"🚫 {mac} ist keine gültige MAC-Adresse")
                return

            device_id = self.db.insert_device(mac)
            if isinstance(device_id, int):
                self.db.insert_netzwerkteilnahme(network_id, device_id)
                say(f"✅ Gerät hinzugefügt.")

        def insert_device(network_id):
            mac = ask("Wie lautet die MAC-Adresse des Geräts?")

            insert_geraet_by_mac(network_id, mac)

        def distribute_checklist_network(network_id, json_data):

            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:
                distribute_checklist(device.id, json_data)

        def add_credentials_network(network_id, credentials: tuple):
            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:
                add_credentials(device.id, credentials)

        def remove_credentials_network(network_id):
            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:

                remove_credentials(device.id)

        def remove_checklists_network(network_id):
            devices = self.db.select_devices(network_id)

            assert(isinstance(devices, list))
            assert(devices)

            for device in devices:
                remove_checklists(device.id)

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
            say(f"✅ Gerät {device_id} gelöscht.")

        def ask_for_checklist_filepath():
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

            return json_data

        def ask_for_credentials() -> tuple:
            user = ask("Nutzername?")
            password = ask("Passwort?")
            correct = ask(f"Nutzer: {user}\nPasswort: {password}\n\nRichtig? (j/n)")

            if not correct in ['j', 'y', 'ja', 'yes']:
                return ()

            return (user, password)

        def distribute_checklist(device_id, json_data):
            self.db.insert_checkliste(json.dumps(json_data), device_id)
            say(f"✅ Checklist zu {device_id} hinzugefügt.")

        def add_credentials(device_id: int, credentials: tuple):
            username = credentials[0]
            password = credentials[1]
            user_id = self.db.insert_benutzer(username, password)

            assert(isinstance(user_id, int))

            self.db.insert_anmeldung(device_id, user_id)
            say(f"✅ Nutzer '{username}' für {device_id} hinterlegt.")

        def remove_credentials(device_id):
            sql = f"""
            SELECT benutzer_id FROM anmeldungen
            WHERE geraet_id = {device_id};
            """

            row_user_ids = self.commit_sql(sql)

            sql = f"""
            DELETE FROM anmeldungen
            WHERE geraet_id = {device_id};
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

                say(f"✅ Nutzer '{user_id}' für {device_id} entfernt.")

        def remove_checklists(device_id):
            sql = f"""
            DELETE FROM checklisten
            WHERE geraet_id = {device_id};
            """

            self.commit_sql(sql)
            say(f"✅ Checklisten gelöscht für Gerät {device_id}.")

        def execute_terminal_command(command, username, password, host, port=22):

            try:
                print(f"[+] Verbinde mit {host}...")

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port, username, password)

                print("[+] Sende Befehl...")
                stdin, stdout, stderr = ssh.exec_command(command)
                stdin.write(password + '\n')  # sudo-Passwort
                stdin.flush()

                print("[✓] Befehl gesendet.")
                ssh.close()
            except Exception as e:
                print("[✗] Fehler:", e)

        def edit_device(device_id):
            text = "1 - Checkliste auslegen\n"\
            "2 - Credentials hinterlegen\n"\
            "3 - Credentials löschen\n"\
            "4 - Checklisten löschen\n"\
            "5 - Terminalkommando ausführen (SSH)"

            choice = ask(text)

            match choice:
                case '1':
                    distribute_checklist(device_id, ask_for_checklist_filepath())
                case '2':
                    add_credentials(device_id, ask_for_credentials())
                case '3':
                    remove_credentials(device_id)
                case '4':
                    remove_checklists(device_id)
                case '5':
                    command = ask("Welches Kommando soll ich ausführen?")
                    res = self.db.select_geraet(device_id)
                    if not res:
                        print(f"Es wurden keine Nutzerdaten für {device_id} gefunden.")
                    else:
                        username = res[0][10]
                        password = res[0][11]
                        host = res[0][2]
                        execute_terminal_command(command, username, password, host)

        def parse_liste(liste_pfad):
            """
            Liest eine Datei mit dem gegebenen Pfad ein, filtert alle MAC-Adressen heraus
            und gibt sie als Python-Liste zurück.

            :param liste_pfad: Pfad zur Textdatei
            :return: Liste von MAC-Adressen
            """
            mac_adressen = []

            # Regulärer Ausdruck für MAC-Adressen (z. B. 00:1A:2B:3C:4D:5E oder 00-1A-2B-3C-4D-5E)
            mac_regex = re.compile(r'(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}')

            try:
                with open(liste_pfad, 'r') as file:
                    for line in file:
                        gefundene_macs = mac_regex.findall(line)
                        mac_adressen.extend(gefundene_macs)
            except FileNotFoundError:
                print(f"Datei nicht gefunden: {liste_pfad}")
            except Exception as e:
                print(f"Fehler beim Verarbeiten der Datei: {e}")

            return mac_adressen

        def edit_network(network_id):

            def run_command_on_device(device, command):
                username = device.benutzer
                password = device.passwort
                host = device.ip
                return execute_terminal_command(command, username, password, host)

            text = "1 - Gerät hinzufügen\n"\
            "2 - Checkliste auslegen (für alle Geräte im Netzwerk)\n"\
            "3 - Credentials hinterlegen (für alle Geräte im Netzwerk)\n"\
            "4 - Credentials löschen (für alle Geräte im Netzwerk)\n"\
            "5 - Checklisten löschen (für alle Geräte im Netzwerk)\n"\
            "6 - Gerät entfernen\n"\
            "7 - Gerät bearbeiten\n"\
            "8 - Terminalkommando ausführen (SSH)\n"\
            "9 - Geräte aus Liste hinzufügen"

            choice = ask(text)

            match choice:
                case '1':
                    insert_device(network_id)
                case '2':
                    distribute_checklist_network(network_id, ask_for_checklist_filepath())
                case '3':
                    add_credentials_network(network_id, ask_for_credentials())
                case '4':
                    remove_credentials_network(network_id)
                case '5':
                    remove_checklists_network(network_id)
                case '6':
                    remove_device(choose_device(network_id))
                case '7':
                    edit_device(choose_device(network_id))
                case '8':
                    command = ask("Welches Kommando soll ich ausführen?")
                    devices = self.db.select_devices(network_id)
                    max_threads = 10

                    with ThreadPoolExecutor(max_workers=max_threads) as executor:
                        # Starte alle Tasks parallel
                        futures = [executor.submit(run_command_on_device, device, command) for device in devices]

                        # Optional: Ergebnisse abwarten und verarbeiten
                        for future in as_completed(futures):
                            try:
                                result = future.result()
                                print(f"Ergebnis: {result}")
                            except Exception as e:
                                print(f"Fehler beim Ausführen: {e}")
                case '9':
                    liste_pfad = ask("Wo ist die Liste gespeichert?").strip()
                    list_geraete = parse_liste(liste_pfad)
                    for mac in list_geraete:
                        insert_geraet_by_mac(network_id, mac)

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
