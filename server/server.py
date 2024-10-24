import socket
import threading
import time
import geraet
from netsweep import NetSweep
import json
import argparse
from urllib.parse import quote, unquote
import traceback
from server_tools import ServerTools

class Server:

    def __init__(self, interface, port, netzwerk_id, attempts, verbose, max_threads):
        self.hinterface = interface
        self.port = port
        self.netzwerk_id = netzwerk_id

        self.clients = []
        self.stop_event = threading.Event()
        self.server_socket = None

        self.netSweep = NetSweep(self.notify_clients, attempts, verbose, max_threads)

    def start(self):

        self.netSweep.sweep(self.netzwerk_id)

        """Startet den Server und akzeptiert eingehende Verbindungen."""
        self.setup_server_socket()

        print(f"Server läuft auf Port {self.port}...")
        while not self.stop_event.is_set():
            self.accept_new_connections()
            time.sleep(0.1)
        self.shutdown_server()

    def setup_server_socket(self):
        """Richtet den Server-Socket ein."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.hinterface, self.port))
        self.server_socket.listen(5)

    def accept_new_connections(self):
        """Akzeptiert neue eingehende Verbindungen."""
        if self.server_socket is None:
            return

        try:
            self.server_socket.settimeout(1)
            client_socket, addr = self.server_socket.accept()
            print(f"Verbindung von {addr} erhalten")
            self.clients.append(client_socket)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()
        except socket.timeout:
            pass

    def handle_client(self, client_socket):
        """Verarbeitet die Kommunikation mit einem verbundenen Client."""
        self.notify_clients() # send initial data
        while not self.stop_event.is_set():
            try:
                client_socket.settimeout(1)  # Timeout setzen, um blockierendes Warten zu vermeiden
                data = client_socket.recv(1024)
                if not data:
                    break
                self.process_client_data(client_socket, data)
            except socket.timeout:
                continue  # Bei Timeout weiterlaufen, um die Schleife nicht unnötig zu belasten
            except Exception as e:
                print(f"Ein Fehler ist aufgetreten: {e}")
                traceback.print_exc()
                break
        self.remove_client(client_socket)

    def process_client_data(self, client_socket, data):
        """Verarbeitet die vom Client empfangenen Daten."""
        print(f"got message '{data}' from {client_socket}")
        # Decode the bytestring to a string
        data_str = data.decode('utf-8')  # Convert bytes to string

        # Now load the JSON
        json_data = json.loads(data_str)

        checklist_id = json_data["checklist_id"]
        pfad = list(map(lambda x: unquote(x), filter(lambda x: x != "" ,json_data["pfad"].split("/"))))
        erledigt = json_data["erledigt"]

        self.update_aufgaben(checklist_id, pfad, erledigt)
        self.notify_clients()

    def remove_client(self, client_socket):
        """Entfernt den Client aus der Liste und schließt den Socket."""
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()

    def notify_clients(self):
        """Benachrichtigt alle verbundenen Clients mit neuen Daten."""

        def list_to_json(geraete_liste):
            # Definiere die JSON-Struktur
            json_liste = []

            for geraet in geraete_liste:

                def parse_checklisten(geraet_id):
                    res = {}

                    row = self.netSweep.db.select_checklists_by_device(geraet_id)
                    # print(len(row))
                    # quit()
                    if isinstance(row, list) and row:
                        for el in row:
                            checklist_id = el[0]
                            checklist = el[1]
                            res[checklist_id] = json.loads(checklist)

                    if res:
                        return res
                    else:
                        return None

                json_objekt = {
                    "mac": geraet.mac,
                    "ip": geraet.ip,
                    "mdns_name": geraet.mdns_name if geraet.mdns_name is not None else "",  # Füge leeren String hinzu, falls None
                    "dns_name": geraet.dns_name,
                    "vnc_status": bool(geraet.vnc_status),  # Konvertiere zu bool
                    "online_status" : bool(geraet.online_status),
                    "benutzer" : geraet.benutzer,
                    "passwort" : geraet.passwort,
                    "checklisten" : parse_checklisten(geraet.id),
                    "id": geraet.id
                }
                json_liste.append(json_objekt)

            # Konvertiere die Liste von JSON-Objekten zu einem JSON-String
            return json.dumps(json_liste, indent=4) + "<END_OF_JSON>"

        # print("Notifying clients...")

        geraete_liste = self.netSweep.db.select_devices(self.netzwerk_id)

        client_data = list_to_json(geraete_liste).encode('utf-8')

        for client in list(self.clients):  # Erstellen einer Kopie der Liste, um während der Iteration Änderungen zu vermeiden
            try:
                client.sendall(client_data)
            except Exception as e:
                print(f"Fehler beim Benachrichtigen eines Clients: {e}")
                self.remove_client(client)

    def update_aufgaben(self, checklist_id, pfad, erledigt):
        """Verarbeitet Aufgaben-Updates (Placeholder)."""
        self.netSweep.db.update_checklist(checklist_id, pfad, erledigt)

    def shutdown_server(self):
        """Fährt den Server herunter und schließt alle Verbindungen."""
        print("Server wird heruntergefahren...")
        self.stop_event.set()
        for client in self.clients:
            client.close()
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":

    def print_logo():

        COLORS = [
            "\033[38;5;214m",  # Annäherung an #F7A93D
            "\033[38;5;203m",  # Annäherung an #DF6552
            "\033[38;5;197m",  # Annäherung an #CE4458
            "\033[38;5;163m",  # Annäherung an #962662
            "\033[38;5;90m"    # Annäherung an #590C68
        ]

        RESET = "\033[0m"

        logo = """
        ▗▖  ▗▖▗▞▀▚▖  ▗▖   ▗▄▄▖▄   ▄ ▗▞▀▚▖▗▞▀▚▖▄▄▄▄
        ▐▛▚▖▐▌▐▛▀▀▘▗▄▟▙▄▖▐▌   █ ▄ █ ▐▛▀▀▘▐▛▀▀▘█   █
        ▐▌ ▝▜▌▝▚▄▄▖  ▐▌   ▝▀▚▖█▄█▄█ ▝▚▄▄▖▝▚▄▄▖█▄▄▄▀lol
        ▐▌  ▐▌       ▐▌  ▗▄▄▞▘                █
                     ▐▌                       ▀
        """

        logo_lines = logo.splitlines()
        print(COLORS[0] + logo_lines[0] + RESET)
        print(COLORS[1] + logo_lines[1] + RESET)
        print(COLORS[2] + logo_lines[2] + RESET)
        print(COLORS[3] + logo_lines[3] + RESET)
        print(COLORS[4] + logo_lines[4] + RESET)



    # Argumente für IP und Port einrichten
    parser = argparse.ArgumentParser(description="Server Script")

    # Make netzwerk_id an optional argument
    parser.add_argument("netzwerk_id", nargs="?", type=int, help="ID of the network to scan (optional)")

    # Optional arguments
    parser.add_argument("--interface", default='0.0.0.0', help="'0.0.0.0' means that the server accepts connections on all available network interfaces of the system. (default: '0.0.0.0')")
    parser.add_argument("--port", default=5000, type=int, help="Port number of the server (default: 5000)")
    parser.add_argument("--attempts", default=5, type=int, help="Choose the number of scan attempts per IP (default: 5)")
    parser.add_argument("--verbose", default=False, type=bool, help="Choose between False and True (default: False)")
    parser.add_argument("--threads", default=100, type=int, help="Choose the maximum number of simultaneous threads (default: 100)")
    parser.add_argument('--reset', action='store_true', help='Reset the system')

    args = parser.parse_args()

    # Print "Hello" if netzwerk_id is not provided
    if args.netzwerk_id is None:

        print_logo()

        st = ServerTools()
        st.setup_database()
        st.show_menu()
    else:
        server = Server(
            args.interface,
            args.port,
            args.netzwerk_id,
            args.attempts,
            args.verbose,
            args.threads,
        )

        server.start()

# python3.11 -m nuitka --standalone --onefile --follow-imports server.py
