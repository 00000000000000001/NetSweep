from typing import Optional, Any
import dearpygui.dearpygui as dpg
import json
import re
import os
from urllib.parse import quote, unquote

from client_socket import ClientSocket

class ClientGUI:
    client_socket = ClientSocket

    def __init__(self, theme='dark'):
        self.window_title = "NetSweep"
        # Farben definieren
        self.yellow_color = [255, 255, 0, 100]  # Gelb mit Transparenz
        self.red_color = [255, 0, 0, 100]       # Rot mit Transparenz
        self.blue_color = [0, 0, 255, 100]      # Rot mit Transparenz
        self.green_color = [0, 255, 0, 100]      # Rot mit Transparenz
        self.white_color = [255, 255, 255, 100]      # Rot mit Transparenz
        self.no_color = [0, 0, 0, 0]            # Keine Färbung (transparent)

        self.erstellte_checklisten_elemente = set()

        # Initialize Dear PyGui context
        dpg.create_context()

        if theme=="light":
            self.set_light_theme()

        # Create main window
        with dpg.window(label="Geräte", width=1200, height=400, no_close=True, tag='window_geraete'):
            with dpg.table(header_row=True,
                row_background=True,
                delay_search=True,
                tag="table",
                borders_innerH=True,
                borders_outerH=True,
                borders_innerV=True,
                borders_outerV=True,
                sortable=True,
                callback=lambda a, b, c: self.sort_callback(a, b),
                resizable=True,
                reorderable=True,
                hideable=True,
                policy=dpg.mvTable_SizingFixedFit,
            ):
                dpg.add_table_column(label="IP")
                dpg.add_table_column(label="MAC")
                dpg.add_table_column(label="DNS-Name")
                dpg.add_table_column(label="mDNS-Name")
                dpg.add_table_column(label="VNC-Status")
                dpg.add_table_column(label="Online-Status")
                dpg.add_table_column(label="Checklisten")

        # Create a viewport and show it
        dpg.create_viewport(title=self.window_title, width=1200, height=400)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def sort_callback(self, sender, sort_specs):

        # sort_specs scenarios:
        #   1. no sorting -> sort_specs == None
        #   2. single sorting -> sort_specs == [[column_id, direction]]
        #   3. multi sorting -> sort_specs == [[column_id, direction], [column_id, direction], ...]
        #
        # notes:
        #   1. direction is ascending if == 1
        #   2. direction is ascending if == -1

        # no sorting case
        if sort_specs is None: return

        rows = dpg.get_item_children(sender, 1)
        columns = dpg.get_item_children(sender, 0)

        col_index = columns.index(sort_specs[0][0])

        # create a list that can be sorted based on first cell
        # value, keeping track of row and value used to sort
        sortable_list = []
        for row in rows:
            first_cell = dpg.get_item_children(row, 1)[col_index]

            if not type(dpg.get_value(first_cell)) in (int, float, str):
                return

            sortable_list.append([row, dpg.get_value(first_cell)])

        def _sorter(e):
            return e[1]

        sortable_list.sort(key=_sorter, reverse=sort_specs[0][1] < 0)

        # create list of just sorted row ids
        new_order = []
        for pair in sortable_list:
            new_order.append(pair[0])

        dpg.reorder_items(sender, 1, new_order)

    def set_light_theme(self):
        with dpg.theme() as light_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (255, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 220, 220))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (220, 220, 220))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (230, 230, 230))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (220, 220, 220))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (220, 220, 220))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (160, 160, 160))
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_Separator, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (160, 160, 160))
                dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, (160, 160, 160))
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (220, 220, 220))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_DockingPreview, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_DockingEmptyBg, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_PlotLines, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_PlotHistogramHovered, (180, 180, 180))
                dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (220, 220, 220))
                dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (220, 220, 220))
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (255, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_DragDropTarget, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_NavHighlight, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_NavWindowingHighlight, (200, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_NavWindowingDimBg, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_ModalWindowDimBg, (240, 240, 240))

        dpg.bind_theme(light_theme)

    def run(self):
        # Start the Dear PyGui event loop
        dpg.start_dearpygui()
        dpg.destroy_context()

    def set_client_socket(self, socket):
            self.client_socket = socket

    def update(self, geraete_liste):
        data = json.loads(geraete_liste)
        self.update_table(data)
        self.color_table()
        self.update_title(data)

    def update_title(self, data):
        def calculate_completed_percentage(data):
            total_tasks = 0
            completed_tasks = 0

            def count_tasks(item):
                nonlocal total_tasks, completed_tasks

                if isinstance(item, dict):
                    for value in item.values():
                        count_tasks(value)
                elif isinstance(item, list):
                    for element in item:
                        if isinstance(element, dict):
                            for task_name, task_completed in element.items():
                                total_tasks += 1
                                if task_completed:
                                    completed_tasks += 1
                        else:
                            count_tasks(element)

            for device in data:
                checklists = device.get('checklisten', {})
                count_tasks(checklists)

            if total_tasks == 0:
                return 0
            else:
                percentage = (completed_tasks / total_tasks) * 100
                return round(percentage, 2)


        network_name = "Network"
        devices_count = dpg.get_item_children("table", 1)
        if devices_count:
            dpg.set_item_label("window_geraete", label=f"{len(devices_count)} interfaces - {len([x for x in data if x['online_status']])} online - {round(calculate_completed_percentage(data), 2)}% done")

    def update_table(self, geraete_liste):

        def add_rows(row_id, geraet):
            dns_name = geraet["dns_name"].removesuffix('.localdomain') if geraet["dns_name"] else ""
            mdns_name = geraet["mdns_name"].removesuffix('.local.') if geraet["mdns_name"] else ""

            index = len(dpg.get_item_children("table", 1)) # Wird von color_table benötigt um den originalen index nach umsortierung zu ermitteln

            with dpg.table_row(tag=f"row_{row_id}", parent="table", user_data=index):
                dpg.add_text(geraet["ip"], tag=f"cell_{row_id}_ip")
                dpg.add_text(geraet["mac"], tag=f"cell_{row_id}_mac")
                dpg.add_text(dns_name, tag=f"cell_{row_id}_dns")
                dpg.add_text(mdns_name, tag=f"cell_{row_id}_mdns")
                self.add_button(geraet, row_id)
                dpg.add_text(geraet["online_status"], tag=f"cell_{row_id}_online")
                self.update_checklists(geraet, row_id)

        def set_rows(row_id, geraet):
            dns_name = geraet["dns_name"].removesuffix('.localdomain') if geraet["dns_name"] else ""
            mdns_name = geraet["mdns_name"].removesuffix('.local.') if geraet["mdns_name"] else ""

            dpg.set_value(f"cell_{row_id}_ip", geraet["ip"])
            dpg.set_value(f"cell_{row_id}_mac", geraet["mac"])
            dpg.set_value(f"cell_{row_id}_dns", dns_name)
            dpg.set_value(f"cell_{row_id}_mdns", mdns_name)
            self.set_button(geraet, row_id)
            dpg.set_value(f"cell_{row_id}_online", geraet["online_status"])
            self.update_checklists(geraet, row_id)

        def delete_rows(geraete_liste):
            children = dpg.get_item_children("table", 1)
            if children:
                for row in children:
                    gesuchte_id = dpg.get_item_alias(row)[4:]
                    if not next((geraet for geraet in geraete_liste if int(geraet["id"]) == int(gesuchte_id)), None):
                        dpg.delete_item(dpg.get_item_alias(row))

        delete_rows(geraete_liste)

        for geraet in geraete_liste:
            row_id = geraet["id"]
            if not dpg.does_item_exist(f"row_{row_id}"):
                add_rows(row_id, geraet)
            else:
                set_rows(row_id, geraet)

    def update_checklists(self, geraet, row_id):

        if not dpg.does_item_exist(f"group_{row_id}"):
            with dpg.group(label="root", tag=f"group_{row_id}"):
                pass

        group_id = f"group_{row_id}"

        def erstelle_checklist_gui_baum(checklisten_dict, parent_element, row_id, checklist_id, pfad=""):

            assert(isinstance(checklist_id, int))

            if not pfad:  # Nur einmal row_id voranstellen
                pfad = f"{checklist_id}"

            for key, value in checklisten_dict.items():
                aktueller_pfad = f"{pfad}/{quote(key, safe='')}"
                if isinstance(value, dict):
                    if aktueller_pfad not in self.erstellte_checklisten_elemente:
                        new_parent = dpg.add_tree_node(label=key, parent=parent_element)
                        self.erstellte_checklisten_elemente.add(aktueller_pfad)
                        erstelle_checklist_gui_baum(value, new_parent, row_id, checklist_id, aktueller_pfad)
                    else:
                        # Falls der Baumknoten existiert, nur rekursiv weitergehen
                        erstelle_checklist_gui_baum(value, parent_element, row_id, checklist_id, aktueller_pfad)
                else:
                    for i, aufgabe in enumerate(value):
                        for aufgabe_text, aufgabe_bool in aufgabe.items():
                            aufgabe_pfad = f"{aktueller_pfad}/{i}"
                            checkbox_id = f"checkbox_{aufgabe_pfad}"

                            if aufgabe_pfad not in self.erstellte_checklisten_elemente:
                                dpg.add_checkbox(
                                    label=aufgabe_text,
                                    default_value=aufgabe_bool,
                                    parent=parent_element,
                                    user_data=aufgabe_pfad,
                                    tag=checkbox_id,
                                    callback=lambda a, b, c: self.checkbox_callback(checklist_id, c, b)
                                )
                                self.erstellte_checklisten_elemente.add(aufgabe_pfad)
                            else:
                                # Falls Checkbox schon existiert, den Status aktualisieren
                                if dpg.does_item_exist(checkbox_id):
                                    dpg.set_value(checkbox_id, aufgabe_bool)


        def markiere_erledigte_tree_nodes(group_id):
            def check_and_mark_tree_node(node_id):
                child_items = dpg.get_item_children(node_id, 1)  # 1 bedeutet, dass wir die direkten Kinder bekommen
                all_checked = True
                all_children_marked = True

                for child in child_items:
                    if dpg.get_item_type(child) == "mvAppItemType::mvCheckbox":
                        # Überprüfen, ob die Checkbox gecheckt ist
                        if not dpg.get_value(child):
                            all_checked = False
                    elif dpg.get_item_type(child) == "mvAppItemType::mvTreeNode":
                        # Rekursiver Aufruf für untergeordnete Baumknoten
                        is_child_marked = check_and_mark_tree_node(child)
                        if not is_child_marked:
                            all_children_marked = False

                # Wenn alle Checkboxen gecheckt sind und alle Kinder markiert sind, füge "DONE: " hinzu
                label = dpg.get_item_label(node_id)
                if all_checked and all_children_marked:
                    if not label.startswith("DONE: "):
                        dpg.set_item_label(node_id, f"DONE: {label}")
                    return True
                else:
                    # Andernfalls "DONE: " entfernen, falls vorhanden
                    if label.startswith("DONE: "):
                        dpg.set_item_label(node_id, label[6:])
                    return False

            # Starte die Überprüfung und Markierung bei der Gruppe
            root_items = dpg.get_item_children(group_id, 1)
            for item in root_items:
                if dpg.get_item_type(item) == "mvAppItemType::mvTreeNode":
                    check_and_mark_tree_node(item)

        checklisten = geraet["checklisten"]
        if not checklisten:
            return


        for el in checklisten.items():

            checklist_id = int(el[0])
            checklist = el[1]
            erstelle_checklist_gui_baum(checklist, group_id, row_id, checklist_id)

        markiere_erledigte_tree_nodes(group_id)


    def add_button(self, geraet, row_id):

        def execute_terminal_command(s, u, a):
            print(f"executing terminal command: {osascript_command}")
            os.system(f'osascript -e \'{osascript_command}\'')

        benutzer = geraet["benutzer"].replace(" ", "%20") if geraet["benutzer"] else ""
        passwort = geraet["passwort"]
        ip = geraet["ip"]

        if benutzer != "" and passwort == "":
            osascript_command = f'do shell script "open vnc://{benutzer}@{ip}"'
        elif benutzer == "" and passwort == "":
            osascript_command = f'do shell script "open vnc://{ip}"'
        else:
            osascript_command = f'do shell script "open vnc://{benutzer}:{passwort}@{ip}"'

            dpg.add_button(
                label=geraet["vnc_status"],
                width=50,
                callback=lambda s, u, a: execute_terminal_command(s, u, a),
                tag=f"button_{row_id}"
            )

    def set_button(self, geraet, row_id):
        dpg.set_item_label(f"button_{row_id}", geraet["vnc_status"])

    def checkbox_callback(self, checklist_id, pfad, erledigt):

        print(checklist_id)

        assert(isinstance(checklist_id, int))

        data = {
            "checklist_id" : checklist_id,
            "pfad" : "/".join(pfad.split("/")[1:]),
            "erledigt": erledigt
        }

        print(data)

        self.client_socket.send_message(json.dumps(data))

    def add_checkbox(self, aufgabe, checklist_id):
        name_aufgabe = aufgabe["name"]
        erledigt = aufgabe["erledigt"]
        aufgabe_id = aufgabe["id"]

        cb_id = dpg.add_checkbox(
            label=name_aufgabe,
            user_data=aufgabe_id,
            callback=self.checkbox_callback,
            tag=f"checkbox_{aufgabe_id}",
            parent=checklist_id)

        dpg.set_value(f"checkbox_{aufgabe_id}", erledigt)

    def set_checkbox(self, aufgabe, checklist_id):
        name_aufgabe = aufgabe["name"]
        erledigt = aufgabe["erledigt"]
        aufgabe_id = aufgabe["id"]

        dpg.set_item_label(f"checkbox_{aufgabe_id}", name_aufgabe)
        dpg.set_value(f"checkbox_{aufgabe_id}", erledigt)

    def color_table(self):
        rows = dpg.get_item_children("table", 1)

        if not rows:
            return

        # Recolor rows based on sorted data, using the correct row number
        for row in rows:
            cols = dpg.get_item_children(row, 1)

            if not cols:
                continue

            # Get online_status and vnc_status for the row
            online_status = dpg.get_value(cols[5])
            vnc_status = dpg.get_item_label(cols[4])

            index = dpg.get_item_user_data(row)
            # Recolor based on the actual row index (i)
            if online_status == "False":  # online_status
                dpg.highlight_table_row(table="table", row=index, color=self.red_color)
            elif vnc_status == "False":  # vnc_status
                dpg.highlight_table_row(table="table", row=index, color=self.blue_color)
            else:
                dpg.highlight_table_row(table="table", row=index, color=self.no_color)


    def show_lock_screen(self):
        # Sperrbildschirm anzeigen
        with dpg.window(label="Locked", modal=True, no_close=True):
            dpg.add_text("Connection lost. UI is locked.")
            dpg.add_button(label="Exit", callback=lambda: dpg.stop_dearpygui())

# Create an instance of the SimpleApp class and run the application
if __name__ == "__main__":
    app = ClientGUI()
    app.run()

# python3.11 -m nuitka --standalone --onefile --follow-imports server.py
