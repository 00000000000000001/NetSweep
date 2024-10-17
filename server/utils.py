import re

def normalize_mac_address(mac: str) -> str:
    assert(mac != 'unbekannt')
    # Entferne alle nicht-hexadezimalen Zeichen (z.B. :, -, .)
    parts = re.split('[:-]', mac)

    # Prüfen, ob die Anzahl der Teile korrekt ist (6 Teile)
    if len(parts) != 6:
        raise ValueError(f"Ungültige MAC-Adresse: {mac}")

    # Stelle sicher, dass jeder Teil genau zwei Zeichen lang ist
    normalized_parts = [part.zfill(2).upper() for part in parts]

    # Füge die Teile mit Doppelpunkten zusammen
    normalized_mac = ':'.join(normalized_parts)

    return normalized_mac


def is_valid_mac(mac: str) -> bool:
    # Definiere das Muster für eine gültige MAC-Adresse (6 Gruppen von Hexadezimal-Zahlen)
    mac_pattern = r'^([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2})$'

    # Prüfen, ob das eingegebene Format der MAC-Adresse einem gültigen Muster entspricht
    if re.match(mac_pattern, mac):
        try:
            # Versuche, die MAC-Adresse zu normalisieren
            normalize_mac_address(mac)
            return True
        except ValueError:
            return False
    else:
        return False


def compare_macs(a: str, b: str) -> bool:
    # print(f"vergleiche: {normalize_mac_address(a)} mit {normalize_mac_address(b)}")
    return normalize_mac_address(a) == normalize_mac_address(b)

def is_valid_ipv4(ip):
    regex = r'^([0-9]{1,3}\.){3}[0-9]{1,3}$'
    if re.match(regex, ip):
        parts = ip.split('.')
        for part in parts:
            if int(part) > 255:
                return False
        return True
    return False

def is_valid_subnet_mask(mask):
    regex = r'^((255|254|252|248|240|224|192|128|0)\.){3}(255|254|252|248|240|224|192|128|0)$'
    if re.match(regex, mask):
        parts = list(map(int, mask.split('.')))
        # Überprüfe, ob die Reihenfolge der Oktette korrekt ist
        return parts == sorted(parts, reverse=True) and (255 in parts or 0 in parts)
    return False

def is_valid_checklist(json_data):
    # Prüfe, ob die Wurzel ein Dictionary ist
    if not isinstance(json_data, dict):
        return False, "Wurzel der Checkliste muss ein Dictionary sein."

    # Funktion, um eine Aufgabenliste zu validieren
    def is_valid_task_list(task_list):
        if not isinstance(task_list, list):
            return False, "Aufgabenliste muss eine Liste sein."

        # Jede Aufgabe in der Liste muss ein Dictionary sein mit genau einem Schlüssel (Name) und einem Wert (Bool)
        for task in task_list:
            if not isinstance(task, dict) or len(task) != 1:
                return False, f"Ungültige Aufgabe: {task}. Jede Aufgabe muss ein Dictionary mit genau einem Schlüssel sein."
            for task_name, completed in task.items():
                if not isinstance(task_name, str):
                    return False, f"Ungültiger Aufgabenname: {task_name}. Aufgabenname muss ein String sein."
                if not isinstance(completed, bool):
                    return False, f"Ungültiger Wert für Aufgabe '{task_name}': {completed}. Wert muss ein Bool (True oder False) sein."

        return True, None

    # Rekursive Überprüfung jeder Checkliste
    def is_valid_checklist_recursive(checklist, path="root"):
        if not isinstance(checklist, dict):
            return False, f"Ungültige Struktur an '{path}': Muss ein Dictionary sein."

        for key, value in checklist.items():
            if isinstance(value, list):
                # Wenn der Wert eine Liste ist, muss es sich um eine Aufgabenliste handeln
                valid, error = is_valid_task_list(value)
                if not valid:
                    return False, f"Fehler in Aufgabenliste '{key}' an Pfad '{path}': {error}"
            elif isinstance(value, dict):
                # Wenn der Wert ein Dictionary ist, muss es eine verschachtelte Checkliste sein
                valid, error = is_valid_checklist_recursive(value, f"{path}.{key}")
                if not valid:
                    return False, error
            else:
                return False, f"Ungültiger Wert für '{key}' an Pfad '{path}': Muss entweder eine Liste (Aufgaben) oder ein Dictionary (Checkliste) sein."

        return True, None

    # Starte die Rekursion von der Wurzel
    return is_valid_checklist_recursive(json_data)
