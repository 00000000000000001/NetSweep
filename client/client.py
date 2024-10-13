import socket
from client_socket import ClientSocket
from client_gui import ClientGUI
import threading
import argparse

class Client:

    def __init__(self, ip, port, theme="light"):
        self.ip = ip
        self.port = port
        # Initialisiere Socket und GUI
        self.socket = ClientSocket(ip, port)
        self.gui = ClientGUI(theme)

        # Verknüpfe Socket und GUI miteinander
        self.socket.set_gui(self.gui)
        self.gui.set_client_socket(self.socket)

    def run(self):
        # Erstelle und starte den Socket-Thread
        socket_thread = threading.Thread(target=self.socket.run)
        socket_thread.start()

        try:
            # Starte die GUI und blockiere, bis sie beendet wird
            self.gui.run()
        finally:
            # Wenn die GUI beendet wird, beenden wir den Socket
            self.socket.stop()
            socket_thread.join()

if __name__ == "__main__":
    # Argumente für IP und Port einrichten
    parser = argparse.ArgumentParser(description="Client Script")
    parser.add_argument("ip", type=str, help="IP address of the server")
    parser.add_argument("port", type=int, help="Port number of the server")

    # Optionales Argument für das Theme hinzufügen
    parser.add_argument("--theme", choices=["light", "dark"], default="light", help="Choose between 'light' or 'dark' theme (default: 'light')")

    # Argumente parsen
    args = parser.parse_args()

    # Client mit den übergebenen Argumenten starten
    client = Client(args.ip, args.port, theme=args.theme)
    client.run()
