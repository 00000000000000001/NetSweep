import socket
from queue import Queue, Empty
import threading
import time
from typing import Optional

class ClientSocket:

    gui = Optional[any]

    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None
        self.queue = Queue()
        self.stop_event = threading.Event()
        self.connection_status = {"connected": False}

    def set_gui(self, gui):
        self.gui = gui

    def create_socket(self):
        """Erstellt einen neuen Socket."""
        if self.client_socket:
            self.client_socket.close()  # Socket schließen, wenn er existiert
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def attempt_reconnect(self):
        """Versucht, die Verbindung zum Server wiederherzustellen."""

        while not self.stop_event.is_set() and not self.connection_status["connected"]:
            self.create_socket()
            try:
                print("Versuche, die Verbindung zum Server wiederherzustellen...")
                self.client_socket.connect((self.server_ip, self.server_port))
                self.connection_status["connected"] = True
                print("Erfolgreich mit dem Server verbunden.")
            except socket.error:
                print("Verbindung fehlgeschlagen, versuche es in 5 Sekunden erneut...")
                # self.gui.show_lock_screen()
                time.sleep(5)  # Pause zwischen den Wiederverbindungsversuchen

    def listen_for_updates(self):
        """Hört auf Nachrichten vom Server und verarbeitet sie."""

        data_buffer = ""
        while not self.stop_event.is_set():
            try:
                self.client_socket.settimeout(1.0)
                response = self.client_socket.recv(1024)
                if not response:
                    self.connection_status["connected"] = False
                    break
                data_buffer += response.decode('utf-8')
                while '<END_OF_JSON>' in data_buffer:
                    complete_message, data_buffer = data_buffer.split('<END_OF_JSON>', 1)
                    self.queue.put(complete_message)
                # data_buffer = ""
            except socket.timeout:
                continue
            except socket.error as e:
                print(f"Fehler beim Empfang von Daten: {e}")
                self.connection_status["connected"] = False
                break
            except Exception as e:
                print(f"Allgemeiner Fehler beim Empfang von Daten: {e}")
                self.connection_status["connected"] = False
                break

    def handle_reconnection(self):
        """Überwacht die Verbindung und startet den Listener neu bei einer Wiederverbindung."""
        while not self.stop_event.is_set():
            if not self.connection_status["connected"]:
                self.attempt_reconnect()
                if self.connection_status["connected"]:
                    listener_thread = threading.Thread(target=self.listen_for_updates)
                    listener_thread.start()
            time.sleep(1)  # Kurze Pause einlegen, um CPU-Verbrauch zu verringern

    def process_queue(self):
        """Verarbeitet die empfangenen Daten aus der Queue."""
        while not self.stop_event.is_set():
            try:
                # Warte auf ein Element in der Queue mit einem Timeout
                geraete_uebersicht = self.queue.get(timeout=1)
                # print(geraete_uebersicht)
                if self.gui:
                    self.gui.update(geraete_uebersicht)
            except Empty:
                continue  # Keine Daten in der Queue, Schleife erneut durchlaufen

    def send_message(self, message: str):
        """Sendet eine Nachricht an den Server."""
        if self.connection_status["connected"] and self.client_socket:
            try:
                self.client_socket.sendall(message.encode('utf-8'))
                print(f"Nachricht gesendet: {message}")
            except socket.error as e:
                print(f"Fehler beim Senden der Nachricht: {e}")
        else:
            print("Nicht mit dem Server verbunden. Nachricht konnte nicht gesendet werden.")

    def run(self):
        """Startet den Client und verwaltet die Verbindung."""
        self.attempt_reconnect()

        if self.connection_status["connected"]:
            listener_thread = threading.Thread(target=self.listen_for_updates)
            listener_thread.start()

            queue_processor_thread = threading.Thread(target=self.process_queue)
            queue_processor_thread.start()

            reconnection_thread = threading.Thread(target=self.handle_reconnection)
            reconnection_thread.start()

            listener_thread.join()
            queue_processor_thread.join()
            reconnection_thread.join()

        self.stop_event.set()
        if self.client_socket:  # Überprüfen, ob client_socket nicht None ist
            self.client_socket.close()

    def stop(self):
        self.stop_event.set()
        if self.client_socket:  # Überprüfen, ob client_socket nicht None ist
            self.client_socket.close()

if __name__ == "__main__":
    client = ClientSocket()
    client.run()
