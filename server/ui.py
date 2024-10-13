from datenbank import Datenbank
import re
from typing import List

db = Datenbank(None)
avatar = '🧌'

def say(msg):
    border = "-" * len(msg)
    print(f"\n{avatar}\n{border}\n{msg}\n{border}\n")

def ask(question: List):
    laengster_string = max(question, key=len)
    border = "-" * len(laengster_string.strip())

    return input(f"\n{avatar}\n{border}\n{"\n".join(question)}\n{border}\n> ")

def main_menu():
    while True:
        frage = [
            "Hallo, was kann ich für dich tun?",
            "",
            "1. Netzwerk hinzufügen",
            "2. Netzwerk bearbeiten",
            "3. Netzwerk entfernen",
            "4. Datenbank zurücksetzen",
            "5. beenden"
        ]

        choice = ask(frage)

        if choice in ('1', "hinzufügen", "Netzwerk hinzufügen"):
            submenu_2()
        elif choice in ('2', "bearbeiten", "Netzwerk bearbeiten"):
            submenu_nw_bearb()
        elif choice in ('3', "entfernen", "Netzwerk entfernen"):
            say("Später...")
        elif choice in ('4', "zurücksetzen", "Datenbank zurücksetzen"):
            submenu_1()
        elif choice in ('5', "beenden"):
            break
        else:
            say("Ungültige Auswahl, bitte erneut versuchen.")

def submenu_1():

    antwort = ask([f"🚸 Sicher? Alle Daten werden dann gelöscht!"])
    if not antwort[:1].lower() in ('j', 'y'):
        say("Operation abgebrochen.")
        return
    antwort = ask([f"WIRKLICH?"])
    if not antwort[:1].lower() in ('j', 'y'):
        say("Operation abgebrochen.")
        return

    db.drop_all_tables()
    db.create_sqlite_database()
    db.create_tables()

def submenu_2():

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

    while True:
        name = ask(["Wie ist der Name des Netzwerkes?"])
        basis_ip = ask(["Ok. Wie ist seine Basis-IP?"])
        while True:
            if is_valid_ipv4(basis_ip):
                break
            else:
                basis_ip = ask([f"⛔️ Die Basis-IP {basis_ip} ist ungültig!", "Wie ist seine Basis-IP?"])

        subnetzmaske = ask(["Wie lautet die Subnetzmaske?"])
        while True:
            if is_valid_subnet_mask(subnetzmaske):
                break
            else:
                subnetzmaske = ask([f"⛔️ Die Subnetzmaske {subnetzmaske} ist ungültig!", "Wie lautet die Subnetzmaske?"])

        db.insert_network(basis_ip, subnetzmaske, name)
        break

def submenu_nw_bearb():

    def find_netzwerk_by_id(liste_netzwerke, id: int):
        for netzwerk in liste_netzwerke:
            if int(netzwerk[3]) == id:
                return netzwerk
        return None

    while True:
        result = db.select_netzwerke()
        str_liste = []
        if result and isinstance(result, list):
            for geraet in result:
                str_liste.append(f"[{geraet[3]}] {geraet[2]}")
            str_liste.insert(0, "Hier ist eine Liste aller Netzwerke:\n")
            str_liste.append("\nWähle eine [ID] zum fortfahren!")
            choice = ask(str_liste)


            try:
                int(choice)
            except:
                say(f"{choice} ist keine gültige id!")
                continue

            netzwerk = find_netzwerk_by_id(result, int(choice))


            if not netzwerk:
                say(f"Eine Netzwerk-ID {choice} existiert nicht!")
                continue

            choice = ask([
                f"Du hast {netzwerk} gewählt.",
                "",
                "Was kann ich für dich tun?",
                "",
                "1. Geraet hinzufügen",
                "2. Geraet bearbeiten",
                "3. Geraet entfernen",
                "4. zurück"
                ])

            netzwerk_id = netzwerk[3]

            if choice in ("1"):
                submenu_4(netzwerk_id)
            elif choice in ("2"):
                geraete = db.select_devices(netzwerk_id)
                if isinstance(geraete, List):
                    choice = ask([f"[{g.id}] {g.mac} {g.ip}" for g in geraete])
                    submenu_geraet_bearbeiten(choice, netzwerk_id)
            elif choice in ("3"):
                geraete = db.select_devices(netzwerk_id)
                if isinstance(geraete, List):
                    choice = ask([f"[{g[0]}] {g[1]} {g[2]}" for g in geraete])
                    db.delete_geraet(choice)

        else:
            say(f"Ich konnte keine Netzwerke finden.")
            break

def submenu_4(netzwerk_id):

    def mac_ist_gueltig(mac):
        # Definiere das Muster einer gültigen MAC-Adresse
        mac_muster = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')

        # Prüfe, ob die MAC-Adresse dem Muster entspricht
        if mac_muster.match(mac):
            return True
        else:
            return False

    while True:
        mac = ask([
            "Wie lautet die MAC-Adresse des Gerätes?"
        ])

        while not mac_ist_gueltig(mac):
            mac = ask([
                f"'{mac}' ist keine gültige MAC-Adresse.",
                "Wie lautet die MAC-Adresse des Gerätes?"
            ])
            break

        geraet_id = db.insert_device(mac)
        db.insert_netzwerkteilnahme(netzwerk_id, geraet_id)
        break

def submenu_geraet_bearbeiten(geraet_id, netzwerk_id):
    while True:
        choice = ask([
            "1. Checkliste erstellen",
            "2. Checkliste bearbeiten",
            "3. Checkliste entfernen",
            "6. Benutzer hinzufügen",
            "7. Benutzer ändern",
            "4. MAC ändern",
            "5. zurück",
        ])

        if choice in ("1"):
            name = ask([
                "Wie soll die Checklist heißen?"
            ])

            db.insert_checkliste(name, geraet_id)
        elif choice in ("2"):
            rows = db.select_checklist(geraet_id)
            if isinstance(rows, List):
                choice = ask([f"[{c[0]}] {c[1]}" for c in rows])
                submenu_aufgaben(choice, netzwerk_id, geraet_id)
        elif choice in ("3"):
            rows = db.select_checklist(geraet_id)
            if isinstance(rows, List):
                choice = ask([f"[{c[0]}] {c[1]}" for c in rows])
            db.delete_checkliste(choice)
        elif choice in ("6"):
            submenu_add_user(geraet_id)
        elif choice in ("7"):
            submenu_edit_user(geraet_id)

        break

def submenu_edit_user(geraet_id):
    rows = db.select_user(geraet_id)
    if isinstance(rows, List):
        benutzer_id = ask([f"[{c[0]}] {c[1]}" for c in rows])
        db.delete_benutzer(benutzer_id)

def submenu_add_user(geraet_id):
    benutzer = ask([
        "Name des Benutzers?"
    ])
    passwort = ask([
        "Passwort des Benutzers?"
    ])

    benutzer_id = db.insert_benutzer(benutzer, passwort)
    db.insert_anmeldung(geraet_id, benutzer_id)

def submenu_aufgaben(checkliste_id, netzwerk_id, geraet_id):

    def checkliste_verteilen(checkliste_id: int, netzwerk_id: int, geraet_id: int):
        rows_checklist = db.commit_sql(f"""
            SELECT name FROM checklisten
            WHERE id = {checkliste_id};
            """)

        if isinstance(rows_checklist, List) and not rows_checklist == []:
            checkliste_name = rows_checklist[0][0]
        else:
            say(f"Ähm...")
            return

        # print(rows_checklist)

        rows_aufgaben = db.commit_sql(f"""
            SELECT beschreibung, erledigt FROM aufgaben
            WHERE checkliste_id = {checkliste_id};
            """)

        # print(rows_aufgaben)

        rows_geraete = db.commit_sql(f"""
            SELECT * FROM geraete AS a
            JOIN netzwerkteilnahmen AS b
            WHERE a.id = b.geraet_id
            AND b.netzwerk_id = 1;
            """)

        # print(rows_geraete)

        if isinstance(rows_geraete, List):
            for g in rows_geraete:
                if not int(g[0]) == int(geraet_id):
                    new_checklist_id = db.insert_checkliste(checkliste_name, g[0])
                    if isinstance(rows_aufgaben, List):
                        for a in rows_aufgaben:
                            db.insert_aufgabe(a[0], a[1], new_checklist_id)
                else:
                    print(f"{g} übersprungen")



    while True:
        choice = ask([
            "1. Aufgabe erstellen",
            "2. Aufgabe bearbeiten",
            "3. Aufgabe löschen",
            "4. Checkliste an alle Gereate verteilen",
        ])

        if choice in ("1"):
            name = ask([
                "Wie lautet die Aufgabe?"
            ])
            db.insert_aufgabe(name, False, checkliste_id)
        elif choice in ("2"):
            rows = db.select_aufgaben(checkliste_id)
            if rows == []:
                say("Es gibt keine Aufgaben.")
            elif isinstance(rows, List):
                aufgabe_id = ask([f"[{a[0]}] {a[1]}" for a in rows])
        elif choice in ("3"):
            say("Später mal...")
        elif choice in ("4"):
            choice = ask(["Alles klar, kanns los gehen?"])
            if choice[:1] in ("j", "y"):
                checkliste_verteilen(checkliste_id, netzwerk_id, geraet_id)
        break


if __name__ == "__main__":
    main_menu()
