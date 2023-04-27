#!/usr/bin/env python3
import json
import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3
import tkinter as tk

# Su GNOME ed altri (su GTK e QT con le librerie di compatibilità)
#   DIPENDENZE:
#       installare => sudo apt-get install gir1.2-appindicator3-0.1


# os.system("pkexec nautilus .")

''' ~/.config/autostart/my-applet.desktop

[Desktop Entry]
Type=Application
Exec=/path/to/my-applet.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=My Applet
Comment=My custom GNOME applet
'''

# recupero percorso attuale (così posso usare un percorso relativo
# in "set_icon_full" per puntare la root di questa app)
PATH_ROOT = os.path.dirname(os.path.realpath(__file__)) #os.popen('realpath .').read().split('\n')[0]

ROOT_APP = PATH_ROOT #"/usr/local/PepAppsLinks"
CONFIG_PATH = '{}/store.json'.format(ROOT_APP)

class MyLinuxApplet:
    # -----------------------------------------------------------------------
    def __init__(self):
        self.app = AppIndicator3.Indicator.new("my-indicator", "", AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        # set icona da percorso personalizzato (ignorando quelle
        # specificate in "AppIndicator3.Indicator.new")
        #   - non solo SVG
        self.app.set_icon_full("{}/icons/icons_security.svg".format(PATH_ROOT), "Icon name")
        self.app.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.app.set_menu(self.init_menu())
        Gtk.main()
    
    # -----------------------------------------------------------------------
    def new_menu_cmd(self, menu, d_glob, d_loc):
        # creo dinamicamente le funzioni e i riferimenti li pusho in "pool_f"
        pool_f = []
        for d in d_loc:
            # gruppo
            if 'items' in d:
                pool_f.append([d['name'], None, d['items']])
            # voce menu
            else:
                ct = d['cmd']
                if d['terminal']:
                    # QUESTO SOTTO funziona quando lo avvio da terminale
                    # gnome-terminal -- bash -c 'ls; exec bash'
                    ct = "gnome-terminal -- bash -c \'{}; exec bash\'".format(ct)
                ct = 'def nf_{}(s):\n\tos.system("{}")'.format(str(len(pool_f)), ct) #cd['cmd'])
                exec(ct)
                cmd = 'pool_f.append(["{}", nf_{}, None])'.format(d['name'], str(len(pool_f)))
                exec(cmd)
        
        # disegna comandi salvati, associando la action\funzione creata prima ad-hoc nel "pool_f"
        for pf in pool_f:
            # sottomenu
            if pf[1] in [None, ""]:
                item = Gtk.ImageMenuItem.new_with_label(pf[0])
                submenu = Gtk.Menu()
                item.set_submenu(self.new_menu_cmd(submenu, d_glob, pf[2]))
                #item.connect("activate", pf[1])
                menu.append(item)
            # voce
            else:
                item = Gtk.ImageMenuItem.new_with_label(pf[0])
                item.connect("activate", pf[1])
                menu.append(item)
        
        self.new_menu_actions(menu, d_glob, d_loc)
        
        return menu
    
    # -----------------------------------------------------------------------
    def new_menu_actions(self, menu, d_glob, d_loc):
        #print(json.dumps(config_data))

        # separatore
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)

        # menu a scomparsa
        item = Gtk.MenuItem()
        item.set_label("Actions")
        submenu = Gtk.Menu()
        # aggiungi comando
        subitem = Gtk.ImageMenuItem.new_with_label("Add cmd")
        subitem.connect("activate", lambda f: self.add_cmd(d_glob, d_loc))
        # icona
        image = Gtk.Image.new_from_file("{}/icons/add_cmd.svg".format(PATH_ROOT))
        subitem.set_always_show_image(True)
        subitem.set_image(image)
        # append al menu
        submenu.append(subitem)
        
        # aggiungi gruppo comandi
        subitem = Gtk.ImageMenuItem.new_with_label("Add group")
        subitem.connect("activate", lambda f: self.add_grp(d_glob, d_loc))
        # icona
        image = Gtk.Image.new_from_file("{}/icons/add_grp.svg".format(PATH_ROOT))
        subitem.set_always_show_image(True)
        subitem.set_image(image)
        # append al menu
        submenu.append(subitem)

        # edit comandi
        subitem = Gtk.ImageMenuItem.new_with_label("Edit list")
        subitem.connect("activate", lambda f: self.edit_list(d_glob, d_loc))
        # icona
        image = Gtk.Image.new_from_file("{}/icons/edit_list.svg".format(PATH_ROOT))
        subitem.set_always_show_image(True)
        subitem.set_image(image)
        # append al menu
        submenu.append(subitem)
        
        # registro submenu
        item.set_submenu(submenu)
        menu.append(item)

    
    # -----------------------------------------------------------------------
    def init_menu(self):
        config_data = []

        # check esistenza file config
        if not os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "w") as f:
                print("'{}' non esiste, ne ho creato uno nuovo".format(CONFIG_PATH))

        # carica settings da file
        config_file = open(CONFIG_PATH, "r")
        if config_file:
            content = config_file.read()
            if content:
                #print(content)
                config_data = json.loads(content)

        menu = Gtk.Menu()

        # lista comandi con actions
        self.new_menu_cmd(menu, config_data, config_data)

        # separatore
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)
        # quit
        item_quit = Gtk.MenuItem("Chiudi")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu
    
    # -----------------------------------------------------------------------
    def popup_cmd(self):
        def add():
            global values
            values = {"cmd": cmd.get(), "name": name.get(), "terminal": terminal.get()}
            popup.destroy()
        
        def cancel():
            global values
            values = None
            popup.destroy()
        
        popup = tk.Tk()
        popup.geometry("350x150")
        popup.title("Aggiungi comando")

        # --------------------
        # label
        frame0 = tk.Frame(popup)
        frame0.pack(expand=True)
        # -----
        label_0 = tk.Frame(frame0)
        label_0.pack(expand=True)
        label = tk.Label(label_0, text="Label:")
        label.pack(side="left")
        name = tk.Entry(label_0)
        name.pack(side="left")
        # --------------------
        # Comando e checkbox
        frame1 = tk.Frame(popup)
        frame1.pack(expand=True)
        # -----
        frame1_1 = tk.Frame(frame1)
        frame1_1.pack(expand=True)
        label = tk.Label(frame1_1, text="Comando:")
        label.pack(side="left")
        cmd = tk.Entry(frame1_1)
        cmd.pack(side="left")
        # -----
        frame1_2 = tk.Frame(frame1)
        frame1_2.pack(expand=True)
        frame1_2.pack()
        terminal = tk.BooleanVar()
        checkbox = tk.Checkbutton(frame1_2, text="Apri da terminale", variable=terminal)
        checkbox.pack(side="left")
        # --------------------
        # pulsanti
        frame2 = tk.Frame(popup)
        frame2.pack(expand=True)
        # -----
        button_ok = tk.Button(frame2, text="Aggiungi", command=add)
        button_ok.pack(side="left")
        # -----
        button_ko = tk.Button(frame2, text="Annulla", command=cancel)
        button_ko.pack(side="left")

        # from tkinter import ttk
        # separator = ttk.Separator(popup, orient="horizontal")
        # separator.pack(side="bottom", padx=50, fill="y")

        popup.protocol("WM_DELETE_WINDOW", cancel)
        popup.mainloop()
        return values
    
    # -----------------------------------------------------------------------
    def popup_grp(self):
        def add():
            global new_group
            new_group = {"name": grp_name.get(), "items": []}
            popup.destroy()
        
        def cancel():
            global new_group
            new_group = None
            popup.destroy()
        
        popup = tk.Tk()
        popup.geometry("350x150")
        popup.title("Crea comando con nuovo gruppo")

        # --------------------
        # label (nuovo gruppo)
        frame0 = tk.Frame(popup)
        frame0.pack(expand=True)
        # -----
        label_0 = tk.Frame(frame0)
        label_0.pack(expand=True)
        label = tk.Label(label_0, text="Label gruppo:")
        label.pack(side="left")
        grp_name = tk.Entry(label_0)
        grp_name.pack(side="left")
        # --------------------
        # pulsanti
        frame2 = tk.Frame(popup)
        frame2.pack(expand=True)
        # -----
        button_ok = tk.Button(frame2, text="Aggiungi", command=add)
        button_ok.pack(side="left")
        # -----
        button_ko = tk.Button(frame2, text="Annulla", command=cancel)
        button_ko.pack(side="left")

        # from tkinter import ttk
        # separator = ttk.Separator(popup, orient="horizontal")
        # separator.pack(side="bottom", padx=50, fill="y")

        popup.protocol("WM_DELETE_WINDOW", cancel)
        popup.mainloop()
        return new_group
    
    # -----------------------------------------------------------------------
    def popup_editor_json(self, d_loc):
        def save():
            global values
            values = json.loads(frame0.get("1.0", tk.END))
            popup.destroy()
        
        def cancel():
            global values
            values = None
            popup.destroy()
        
        popup = tk.Tk()
        popup.geometry("500x700")
        popup.title("Modifica configurazione")

        # --------------------
        # label (nuovo gruppo)
        frame0 = tk.Text(popup, width=200, height=30)
        frame0.pack(expand=True)
        frame0.insert(tk.END, json.dumps(d_loc, indent=2, sort_keys=False))
        # --------------------
        # pulsanti
        frame2 = tk.Frame(popup)
        frame2.pack(expand=True)
        # -----
        button_ok = tk.Button(frame2, text="Salva", command=save)
        button_ok.pack(side="left")
        # -----
        button_ko = tk.Button(frame2, text="Annulla", command=cancel)
        button_ko.pack(side="left")

        # from tkinter import ttk
        # separator = ttk.Separator(popup, orient="horizontal")
        # separator.pack(side="bottom", padx=50, fill="y")

        popup.protocol("WM_DELETE_WINDOW", cancel)
        popup.mainloop()
        return values
    
    # -----------------------------------------------------------------------
    def add_cmd(self, d_glob, d_loc):
        v = self.popup_cmd()
        if v is None or v['cmd'] in [None, ""]:
            # utente ha annullato
            return

        f = open(CONFIG_PATH, "w")
        obj = {
            "name": v['name'],
            "cmd": v['cmd'],
            "terminal": v['terminal']
        }

        d_loc.append(obj)
        f.write(json.dumps(d_glob))
        f.close()
        self.app.set_menu(self.init_menu())
    
    # -----------------------------------------------------------------------
    def add_grp(self, d_glob, d_loc):
        g = self.popup_grp()
        if g is None or g['name'] in [None, ""]:
            # utente non ha inserito nome gruppo
            return

        f = open(CONFIG_PATH, "w")
        grp = {
            "name": g['name'],
            "items": []
        }

        d_loc.append(grp)
        f.write(json.dumps(d_glob))
        f.close()
        self.app.set_menu(self.init_menu())
    
    # -----------------------------------------------------------------------
    def edit_list(self, d_glob, d_loc):
        #os.system("gnome-text-editor '{}'".format(CONFIG_PATH))
        values = self.popup_editor_json(d_loc)
        if values in [None, ""]:
            # utente ha annullato
            return
        
        if type(d_loc) == type([]):
            d_loc.clear()
            for v in values:
                d_loc.append(v)
        else:
            # Per mantenere il riferimento di "d_loc" in "d_glob" non devo
            # rimpiazzare l'oggetto ma modificarne solo il contenuto:
            #   - rimuovo ogni attributo da d_loc
            keys = d_loc.keys()
            for k in keys:
                del d_loc[k]
            #   - ricreo ogni attributo recuperato dall'editor
            for kv in values:
                d_loc[kv] = values[k]
        
        # aggiorno il file di configurazione
        f = open(CONFIG_PATH, "w")
        f.write(json.dumps(d_glob))
        f.close()
        self.app.set_menu(self.init_menu())

        self.app.set_menu(self.init_menu())

    # -----------------------------------------------------------------------
    def quit(self, source):
        Gtk.main_quit()

# avvio applet
MyLinuxApplet()
