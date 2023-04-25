#!/usr/bin/env python3
import json
import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3
import tkinter as tk
from tkinter import filedialog
import ntpath

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

CONFIG_PATH = 'config.json'
ROOT_APP = "/usr/local/PepAppsManager"
APP_INSTALLED = "apps"
APP_INFO_REMOVE = "apps_uninstall"

# recupero percorso attuale (così posso usare un percorso relativo
# in "set_icon_full" per puntare la root di questa app)
PATH_ROOT = os.popen('realpath .').read().split('\n')[0]

class MyLinuxApplet:
    # -----------------------------------------------------------------------
    def __init__(self):
        self.app = AppIndicator3.Indicator.new("my-indicator", "", AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        # set icona da percorso personalizzato (ignorando quelle
        # specificate in "AppIndicator3.Indicator.new")
        #   - non solo SVG
        self.app.set_icon_full("{}/icons/pepapps.svg".format(PATH_ROOT), "Icon name")
        self.app.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.app.set_menu(self.init_menu())
        #print(self.popup_path_dir())
        #self.popup_path_file()
        Gtk.main()
    
    # -----------------------------------------------------------------------
    def crea_file(self, lines, path):
        f = open(path, "w")
        f.write('\n'.join(lines))
        f.close()

    # -----------------------------------------------------------------------
    def read_config_file(self):
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
        return config_data
    
    # -----------------------------------------------------------------------
    def write_config_file(self, config_data):
        if type(config_data) != type([]):
            config_data = []
        
        # check esistenza file config
        if not os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "w") as f:
                print("'{}' non esiste, ne ho creato uno nuovo".format(CONFIG_PATH))

        f = open(CONFIG_PATH, "w")
        f.write(json.dumps(config_data))
        f.close()

    # -----------------------------------------------------------------------
    def new_menu_cmd(self, menu, d_glob, d_loc):
        self.new_menu_actions(menu, d_glob, d_loc)

        # creo dinamicamente le funzioni e i riferimenti li pusho in "pool_f"
        pool_f = []
        for d in d_loc:
            ct = "" #d['cmd']
            # QUESTO SOTTO funziona quando lo avvio da terminale
            # gnome-terminal -- bash -c 'ls; exec bash'
            ct = "gnome-terminal -- bash -c \'{}; exec bash\'".format(ct)
            ct = 'def nf_{}(s):\n\tos.system("{}")'.format(str(len(pool_f)), ct)
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
        
        return menu
    
    # -----------------------------------------------------------------------
    def new_menu_actions(self, menu, d_glob, d_loc):
        #print(json.dumps(config_data))

        # menu a scomparsa
        item = Gtk.MenuItem()
        item.set_label("Actions")
        submenu = Gtk.Menu()
        # aggiungi comando
        subitem = Gtk.ImageMenuItem.new_with_label("Install")
        #subitem.connect("activate", lambda f: self.add_cmd(d_glob, d_loc))
        subitem.connect("activate", lambda f: self.popup_install())
        
        # icona
        image = Gtk.Image.new_from_file("{}/icons/add_cmd.svg".format(PATH_ROOT))
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

        # separatore
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)

    # -----------------------------------------------------------------------
    def init_menu(self):
        '''
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
        '''
        
        config_data = self.read_config_file()

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
    def popup_info(self, msg):
        def show():
            # Creazione del popup informativo
            popup = tk.Toplevel()
            popup.title("Informazioni")
            popup.geometry("200x100")
            popup.resizable(False, False)

            # Creazione del testo del popup
            label = tk.Label(popup, text=msg) #"Questo è un popup informativo.")
            label.pack(pady=20)

            # Creazione del pulsante di chiusura del popup
            button = tk.Button(popup, text="Chiudi", command=popup.destroy)
            button.pack()

        # Creazione della finestra principale
        popup = tk.Tk()

        # Creazione del pulsante per aprire il popup
        #button = tk.Button(root, text="Mostra popup", command=show)
        #button.pack(pady=20)

        # Creazione del popup informativo
        #popup = tk.Toplevel()
        popup.title("Informazioni")
        popup.geometry("400x100")
        popup.resizable(False, False)

        # Creazione del testo del popup
        label = tk.Label(popup, text=msg) #"Questo è un popup informativo.")
        label.pack(pady=20)

        # Creazione del pulsante di chiusura del popup
        button = tk.Button(popup, text="Chiudi", command=popup.destroy)
        button.pack()


        ###show()

        # Avvio del mainloop di tkinter
        popup.mainloop()
    
    # -----------------------------------------------------------------------
    def popup_path_dir(self):
        def select_folder():
            global folder_path
            folder_path = None
            folder_path = filedialog.askdirectory()
            print("Selected folder:", folder_path)
            root.destroy()

        root = tk.Tk()
        # Creazione del pulsante per aprire la finestra di dialogo
        button = tk.Button(root, text="Seleziona cartella", command=select_folder)
        button.pack(pady=10)
        root.mainloop()
        return folder_path
    
    # -----------------------------------------------------------------------
    def popup_path_file(self):
        def select_file():
            global file_path
            file_path = filedialog.askopenfilename()
            print("Selected file:", file_path)
            root.destroy()

        root = tk.Tk()
        # Creazione del pulsante per aprire la finestra di dialogo
        button = tk.Button(root, text="Seleziona file", command=select_file)
        button.pack(pady=10)
        root.mainloop()
        return file_path
    
    # -----------------------------------------------------------------------
    def flusso_installazione(self, d):
        '''
        {
            "dir": folder_path,
            "exe": file_path,
            "cmd": cmd_exe.get(),
            "autorun": autorun.get(),
            "label": name.get(),
            "icon": path_icona.get()
        }
        '''

        cmds = []

        # fix path cartella
        if d["dir"][-1] != '/':
            d["dir"] = "{}/".format(d["dir"])

        # recupera path relativo exe
        #   - check se "dir" è contenuto in "exe"
        if d["dir"] not in d["exe"]:
            self.popup_info("L\'eseguibile deve essere nella cartella")
            return
        
        if d["cmd"] not in d["exe"]:
            self.popup_info("L\'eseguibile deve essere nella cartella")
            return

        # costruisci il path della cartella da creare
        dest_new_dir = "{}/apps/{}".format(ROOT_APP, d["cmd"])

        # costruisci il link dell'eseguibile sulla cartella copiata
        exe_relativo = d["exe"].split(d["dir"])[1]
        dest_new_exe = "{}/apps/{}".format(ROOT_APP, exe_relativo)
        new_link_exe = "/usr/local/bin/{}".format(d["cmd"])

        # copia cartella app in "/usr/local/PepAppsManager/apps/"
        cmd = "cp {} {}/{}/{}/".format(d["dir"], ROOT_APP, APP_INSTALLED, d["cmd"])
        os.system(cmd)
        # aggancio comando globale ad eseguibile
        cmd = "ln -s {} {}".format(dest_new_exe, new_link_exe)
        os.system(cmd)
        # creo cartella app per info e uninstaller
        uninstaller_dir = "{}/{}/{}/".format(ROOT_APP, APP_INFO_REMOVE, d["cmd"])
        cmd = "mkdir {}".format(uninstaller_dir)
        os.system(cmd)

        #   - genera contenuto script uninstall
        script_uninstall = [
            "#!/bin/sh",
            # main dir
            "rm -R \'{}\'".format(dest_new_dir),
            # rm link
            "rm {}".format(new_link_exe)
        ]

        # crea .desktop
        if d["label"] not in [None, ""]:
            # crea .desktop e script uninstall => registra sul config.json
            #   - genera contenuto .desktop
            file_desktop = [
                "[Desktop Entry]",
                "Version=1.0",
                "Terminal=false",
                "Type=Application",
                "Name={}".format(d["label"]),
                "GenericName={}".format(d["label"]),
                "Exec={}".format(dest_new_exe)
            ]

            if d['autorun'] == True:
                file_desktop.append("Hidden=false")
                file_desktop.append("NoDisplay=false")
                file_desktop.append("X-GNOME-Autostart-enabled=true")

            if d["icon"] not in [None, ""]:
                # copia icona in "/usr/local/PepAppsManager/apps_uninstall/<nuova/"
                icon_name = ntpath.basename(d["icon"])
                dst_icon_file = "{}{}".format(uninstaller_dir, icon_name)
                # copia fisica
                cmd = "cp {} {}".format(d["icon"], dst_icon_file)
                os.system(cmd)
                # inserisco icona nel .desktop
                file_desktop.append("Icon={}".format(dst_icon_file))
            
            #
            dst_cp_desktop_file = "/usr/share/applications/{}.desktop".format(d["cmd"])
            
            # add rimozione .desktop allo script di uninstall
            script_uninstall.append("rm /usr/share/applications/{}.desktop".format(d["cmd"]))

            # crea e copia .desktop in "/usr/share/applications"
            self.crea_file(file_desktop, dst_cp_desktop_file)

            if d['autorun'] == True:
                dst_cp_desktop_file_autorun = "~/.config/autostart/{}.desktop".format(d["cmd"])
                # lo copio anche per l'autorun
                self.crea_file(file_desktop, dst_cp_desktop_file_autorun)

        # crea script uninstall in "/usr/local/PepAppsManager/apps_uninstall/<nuova/"
        dst_uninstall_file = "{}{}.sh".format(uninstaller_dir, d["cmd"])
        self.crea_file(script_uninstall, dst_uninstall_file)
        
        config_data = self.read_config_file()
        config_data.append({
            "name": d["label"] if d["label"] not in [None, ""] else d["cmd"],
            "cmd": d["cmd"]
        })

        self.write_config_file(config_data)
        print("FINITO")

    # -----------------------------------------------------------------------
    def popup_install(self):
        def select_folder():
            global folder_path
            folder_path = filedialog.askdirectory()
            path_dir.delete(0, tk.END)  # Rimuove il contenuto esistente
            path_dir.insert(0, folder_path)
            #popup.destroy()
        
        def select_file():
            default = path_dir.get() if path_dir.get() != "" else None
            global file_path
            file_path = filedialog.askopenfilename(initialdir=default)
            path_file.delete(0, tk.END)  # Rimuove il contenuto esistente
            path_file.insert(0, file_path)
            #popup.destroy()
        
        def select_file_icona():
            default = path_dir.get() if path_dir.get() != "" else None
            global file_path_icona
            file_path_icona = filedialog.askopenfilename(initialdir=default)
            path_icona.delete(0, tk.END)  # Rimuove il contenuto esistente
            path_icona.insert(0, file_path_icona)
            #popup.destroy()
        
        def install():
            self.flusso_installazione({
                "dir": path_dir.get(),
                "exe": path_file.get(),
                "cmd": cmd_exe.get(),
                "autorun": autorun.get(),
                "label": name.get(),
                "icon": path_icona.get()
            })
            popup.destroy()
        
        def cancel():
            popup.destroy()
        
        popup = tk.Tk()
        popup.geometry("600x350")
        popup.title("Installazione app")

        # --------------------
        # Path cartella (da copiare in /usr/local/X/dir_nuova_app)
        frame_path_dir = tk.Frame(popup)
        frame_path_dir.pack(expand=True)
        # -----
        label = tk.Label(frame_path_dir, text="(1) Seleziona la cartella con i file e l'eseguibile")
        label.pack()
        # -----
        path_dir = tk.Entry(frame_path_dir, width=50)
        path_dir.pack(side="left")
        button = tk.Button(frame_path_dir, text="Scegli", command=select_folder)
        button.pack(pady=10, side="left")
        # --------------------
        # Path eseguibile
        # -----
        frame_path_exe = tk.Frame(popup)
        frame_path_exe.pack(expand=True)
        # -----
        label = tk.Label(frame_path_exe, text="(2) Seleziona l'eseguibile o lo script di avvio")
        label.pack()
        # -----
        path_file = tk.Entry(frame_path_exe, width=50)
        path_file.pack(side="left")
        button = tk.Button(frame_path_exe, text="Scegli", command=select_file)
        button.pack(pady=10, side="left")
        # --------------------
        # cmd launcher eseguibile
        # -----
        frame_cmd_exe = tk.Frame(popup)
        frame_cmd_exe.pack(expand=True)
        # -----
        label = tk.Label(frame_cmd_exe, text="(3) Scegli un comando per l'avvio da terminale")
        label.pack()
        # -----
        cmd_exe = tk.Entry(frame_cmd_exe, width=20)
        cmd_exe.pack()
        # --------------------
        # Info file .desktop (da copiare in /usr/local/X/dir_nuova_app)
        frame_file_desktop = tk.Frame(popup)
        frame_file_desktop.pack(expand=True)
        # -----
        label = tk.Label(frame_file_desktop, text="(4) Info launcher grafico [Opzionale]")
        label.pack()
        # -----
        l_name = tk.Label(frame_file_desktop, text="Label")
        l_name.pack(side="left")
        name = tk.Entry(frame_file_desktop, width=20)
        name.pack(side="left")
        # -----
        frame_icona = tk.Frame(popup)
        frame_icona.pack(expand=True)
        l_icona = tk.Label(frame_icona, text="Icona")
        l_icona.pack(side="left")
        path_icona = tk.Entry(frame_icona, width=50)
        path_icona.pack(side="left")
        button = tk.Button(frame_icona, text="Scegli", command=select_file_icona)
        button.pack(pady=10, side="left")
        # -----
        # autoavvio con Ubuntu
        frame_autorun = tk.Frame(popup)
        frame_autorun.pack(expand=True)
        frame_autorun.pack()
        autorun = tk.BooleanVar()
        checkbox = tk.Checkbutton(frame_autorun, text="Autoavvia con Ubuntu", variable=autorun)
        checkbox.pack(side="left")

        # --------------------
        # Copia .desktop (/usr/share/applications)
        # -----

        # --------------------
        # pulsanti
        frame2 = tk.Frame(popup)
        frame2.pack(expand=True)
        # -----
        button_ok = tk.Button(frame2, text="Installa", command=install)
        button_ok.pack(side="left")
        # -----
        button_ko = tk.Button(frame2, text="Annulla", command=cancel)
        button_ko.pack(side="left")

        # from tkinter import ttk
        # separator = ttk.Separator(popup, orient="horizontal")
        # separator.pack(side="bottom", padx=50, fill="y")

        popup.protocol("WM_DELETE_WINDOW", cancel)
        popup.mainloop()
        #return values
    
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

        #print("-----")
        #print(json.dumps(obj))
        #print(json.dumps(d_glob))
        #print("-----")
    
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
