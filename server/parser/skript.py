import re
import os

def lexer(text):
    tokens = []

    # Patterns für die verschiedenen Token-Arten
    mac_pattern = re.compile(r"([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})")
    checklist_pattern = re.compile(r"(/[\w/]+\.json)")
    credentials_pattern = re.compile(r"\(([^,]+),\s*([^)]+)\)")

    # Zeilen durchlaufen, um die anderen Tokens zu finden
    lines = text.split('\n')

    for line in lines:
        # Suche nach 'MAC' Token
        mac_match = mac_pattern.search(line)
        if mac_match:
            tokens.append(('MAC', mac_match.group(1)))

        # Suche nach 'CHECKLIST' Token
        checklist_matches = checklist_pattern.findall(line)
        for checklist in checklist_matches:
            tokens.append(('CHECKLIST', checklist))

        # Suche nach 'CREDENTIALS' Token
        credentials_matches = credentials_pattern.findall(line)
        for credentials in credentials_matches:
            tokens.append(('CREDENTIALS', (credentials[0].strip(), credentials[1].strip())))

    return tokens

def foo(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        text =  file.read()

    # Lexer aufrufen
    tokens = lexer(text)

    print(('NETWORK', os.path.splitext(os.path.basename(file_path))[0]))
    for token in tokens:
        print(token)

foo('./system-helden.ns')
