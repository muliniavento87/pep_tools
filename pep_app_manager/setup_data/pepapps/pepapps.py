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
import urllib.parse

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


APP_INSTALLED = "apps"
APP_INFO_REMOVE = "apps_uninstall"

# recupero percorso attuale (così posso usare un percorso relativo
# in "set_icon_full" per puntare la root di questa app)
PATH_ROOT = os.path.dirname(os.path.realpath(__file__)) #os.popen('realpath .').read().split('\n')[0]

ROOT_APP = PATH_ROOT #"/usr/local/PepAppsManager"
CONFIG_PATH = '{}/store.json'.format(ROOT_APP)

PATH_HOME_USER = os.popen('realpath ~').read().split('\n')[0]

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
        Gtk.main()
    
    # -----------------------------------------------------------------------
    def crea_file(self, lines, path):
        cmd = 'echo "{}" > {}'.format('\n'.join(lines), path)
        return cmd
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
        
        def cu(s, c, d):
            # aggiorna voce menu sul JSON
            data = json.dumps(d)
            data = urllib.parse.quote(data)
            c = "sudogui python3 {}/help_uninstaller.py '{}' '{}'".format(PATH_ROOT, c, d)
            result = os.popen(c).read()
            result = urllib.parse.unquote(result)

            # rigenera menu
            s.app.set_menu(self.init_menu())
            print("FINITO")
        

        self.new_menu_actions(menu, d_glob, d_loc)
        
        #exec('\n'.join(f))
        data = json.dumps(d_glob)
        data = urllib.parse.quote(data)
        #cmd = "sudogui python3 {}/help_uninstaller.py '{}' '{}'".format(PATH_ROOT, data)
        #result = os.popen(cmd).read()
        #result = urllib.parse.unquote(result)

        # creo dinamicamente le funzioni e i riferimenti li pusho in "pool_f"
        pool_f = []
        for d in d_loc:
            cmds = [
                #"echo 'aa'",
                "sudogui sh {}/{}/{}/{}.sh".format(ROOT_APP, APP_INFO_REMOVE, d['cmd'], d['cmd']),
                "sudo rm -R {}/{}/{}/".format(ROOT_APP, APP_INFO_REMOVE, d['cmd'], d['cmd']),
                #"sudo python3 {}/help_uninstaller.py '{}' '{}' '{}'".format(PATH_ROOT, CONFIG_PATH, d['cmd'], data)
            ]
            ct = ' && '.join(cmds)
            #ct = 'def nf_{}(s, x):\n\tos.system("{}")\n\ts.app.set_menu(s.init_menu())'.format(str(len(pool_f)), ct)
            ct = 'def nf_{}(x):\n\tos.system("{}")'.format(str(len(pool_f)), ct)
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
                #item.connect("activate", lambda x: pf[1](self, x))
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
        # Creazione della finestra principale
        popup = tk.Tk()
        # Creazione del popup informativo
        popup.title("Informazioni")
        popup.geometry("400x100")
        popup.resizable(False, False)

        # Creazione del testo del popup
        label = tk.Label(popup, text=msg) #"Questo è un popup informativo.")
        label.pack(pady=20)

        # Creazione del pulsante di chiusura del popup
        button = tk.Button(popup, text="Chiudi", command=popup.destroy)
        button.pack()

        # Avvio del mainloop di tkinter
        popup.mainloop()

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

        # fix path cartella
        if d["dir"][-1] != '/':
            d["dir"] = "{}/".format(d["dir"])

        # recupera path relativo exe
        #   - check se "dir" è contenuto in "exe"
        if d["dir"] not in d["exe"]:
            self.popup_info("L\'eseguibile deve essere nella cartella")
            return
        
        if d["cmd"] in [None, '']:
            self.popup_info("L\'eseguibile deve essere nella cartella")
            return
        
        parameters = d.copy()
        parameters["ROOT_APP"] = ROOT_APP
        parameters["CONFIG_PATH"] = CONFIG_PATH
        parameters["APP_INSTALLED"] = APP_INSTALLED
        parameters["APP_INFO_REMOVE"] = APP_INFO_REMOVE
        parameters["PATH_ROOT"] = PATH_ROOT
        parameters["PATH_HOME_USER"] = PATH_HOME_USER
        
        data = json.dumps(parameters)
        data = urllib.parse.quote(data)
        cmd = "sudogui python3 {}/help_installer.py '{}'".format(PATH_ROOT, data)
        result = os.popen(cmd).read()
        result = urllib.parse.unquote(result)

        # rigenera menu
        self.app.set_menu(self.init_menu())
        print("FINITO")

    # -----------------------------------------------------------------------
    def popup_install(self):
        def select_folder():
            default = path_dir.get() if path_dir.get() != "" else "~"
            global folder_path
            folder_path = filedialog.askdirectory(initialdir=default)
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
        # pulsanti
        frame2 = tk.Frame(popup)
        frame2.pack(expand=True)
        # -----
        button_ok = tk.Button(frame2, text="Installa", command=install)
        button_ok.pack(side="left")
        # -----
        button_ko = tk.Button(frame2, text="Annulla", command=cancel)
        button_ko.pack(side="left")

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

    # -----------------------------------------------------------------------
    def quit(self, source):
        Gtk.main_quit()

# avvio applet
MyLinuxApplet()
