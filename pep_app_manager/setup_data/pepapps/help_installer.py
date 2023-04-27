import json
import ntpath
import sys
import os
import urllib.parse

ROOT_APP = ""
CONFIG_PATH = ""
APP_INSTALLED = ""
APP_INFO_REMOVE = ""
PATH_ROOT = ""
PATH_HOME_USER = ""

# -----------------------------------------------------------------------
def read_config_file(path):
    config_data = []

    # check esistenza file config
    if not os.path.exists(path):
        with open(path, "w") as f:
            #print("'{}' non esiste, ne ho creato uno nuovo".format(CONFIG_PATH))
            a = 0

    # carica settings da file
    config_file = open(path, "r")
    if config_file:
        content = config_file.read()
        if content:
            #print(content)
            config_data = json.loads(content)
    return config_data

# -----------------------------------------------------------------------
def write_config_file(config_data, path):
    if type(config_data) != type([]):
        config_data = []
    
    # check esistenza file config
    if not os.path.exists(path):
        with open(path, "w") as f:
            #print("'{}' non esiste, ne ho creato uno nuovo".format(CONFIG_PATH))
            a = 0

    f = open(path, "w")
    f.write(json.dumps(config_data))
    f.close()

# -----------------------------------------------------------------------
def crea_file(lines, path):
    cmd = 'echo "{}" > {}'.format('\n'.join(lines), path)
    return cmd

# -----------------------------------------------------------------------
def flusso_installazione(d_in):
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
    str = urllib.parse.unquote(d_in)
    d = json.loads(str)
    #return json.dumps(a)

    ROOT_APP = d["ROOT_APP"]
    CONFIG_PATH = d["CONFIG_PATH"]
    APP_INSTALLED = d["APP_INSTALLED"]
    APP_INFO_REMOVE = d["APP_INFO_REMOVE"]
    PATH_ROOT = d["PATH_ROOT"]
    PATH_HOME_USER = d["PATH_HOME_USER"]

    '''
    # fix path cartella
    if d["dir"][-1] != '/':
        d["dir"] = "{}/".format(d["dir"])

    # recupera path relativo exe
    #   - check se "dir" è contenuto in "exe"
    if d["dir"] not in d["exe"]:
        popup_info("L\'eseguibile deve essere nella cartella")
        return
    
    if d["cmd"] in [None, '']:
        popup_info("L\'eseguibile deve essere nella cartella")
        return
    '''

    # costruisci il path della cartella da creare
    dest_new_dir = "{}/{}/{}".format(ROOT_APP, APP_INSTALLED, d["cmd"])

    # costruisci il link dell'eseguibile sulla cartella copiata
    exe_relativo = d["exe"].split(d["dir"])[1]
    dest_new_exe = "{}/{}/{}/{}".format(ROOT_APP, APP_INSTALLED, d["cmd"], exe_relativo)
    new_link_exe = "/usr/local/bin/{}".format(d["cmd"])

    cmds = []

    # copia cartella app in "/usr/local/PepAppsManager/apps/"
    cmd = "cp -r {} {}/{}/{}/".format(d["dir"], ROOT_APP, APP_INSTALLED, d["cmd"])
    cmds.append(cmd)
    #os.system(cmd)
    # aggancio comando globale ad eseguibile
    cmd = "ln -s {} {}".format(dest_new_exe, new_link_exe)
    cmds.append(cmd)
    #os.system(cmd)
    # creo cartella app per info e uninstaller
    uninstaller_dir = "{}/{}/{}/".format(ROOT_APP, APP_INFO_REMOVE, d["cmd"])
    cmd = "mkdir {}".format(uninstaller_dir)
    cmds.append(cmd)
    #os.system(cmd)

    #   - genera contenuto script uninstall
    script_uninstall = [
        "#!/bin/sh",
        # main dir
        "rm -R \"{}\"".format(dest_new_dir),
        # rm link
        "rm {}".format(new_link_exe)
    ]

    # crea .desktop
    if d["label"] in [None, ""]:
        d["label"] = d["cmd"]
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
        cmds.append(cmd)
        #os.system(cmd)
        # inserisco icona nel .desktop
        file_desktop.append("Icon={}".format(dst_icon_file))
    
    #
    dst_cp_desktop_file = "/usr/share/applications/{}.desktop".format(d["cmd"])
    
    # add rimozione .desktop allo script di uninstall
    script_uninstall.append("rm /usr/share/applications/{}.desktop".format(d["cmd"]))

    # crea e copia .desktop in "/usr/share/applications"
    cmd = crea_file(file_desktop, dst_cp_desktop_file)
    cmds.append(cmd)

    if d['autorun'] == True:
        dst_cp_desktop_file_autorun = "{}/.config/autostart/{}.desktop".format(PATH_HOME_USER, d["cmd"])
        # lo copio anche per l'autorun
        cmd = crea_file(file_desktop, dst_cp_desktop_file_autorun)
        cmds.append(cmd)
        # add rimozione .desktop allo script di uninstall
        script_uninstall.append("rm {}".format(dst_cp_desktop_file_autorun))

    # crea script uninstall in "/usr/local/PepAppsManager/apps_uninstall/<nuova/"
    dst_uninstall_file = "{}{}.sh".format(uninstaller_dir, d["cmd"])
    cmd = crea_file(script_uninstall, dst_uninstall_file)
    cmds.append(cmd)

    cmd = "chmod -R 777 {}".format(CONFIG_PATH)
    cmds.append(cmd)

    # echo 'passwd' | sudo -S sh -c 'cd /usr && nautilus .'
    #password = "passwd"  # Inserisci la password di root o di un utente con privilegi sudo
    command = ' && '.join(cmds)
    #os.system('echo \'{}\' | sudo -S sh -c \'{}\''.format(password, command))
    os.system(command)

    # non legge il config.json
    # metti un SUDO grafico
    # FIXA ste cose dei permessi

    # sudo rm /usr/local/bin/blender ; sudo rm -r /usr/local/PepAppsManager/apps/blender/ ; sudo rm -r /usr/local/PepAppsManager/apps_uninstall/blender/ ; sudo rm /usr/share/applications/blender.desktop ; sudo rm /home/giuseppe/.config/autostart/blender.desktop
    '''
    sudo rm /usr/local/bin/blender
    sudo rm -r /usr/local/PepAppsManager/apps/blender/
    sudo rm -r /usr/local/PepAppsManager/apps_uninstall/blender/
    sudo rm /usr/share/applications/blender.desktop
    sudo rm /home/giuseppe/.config/autostart/blender.desktop

    sudo chmod -R 777 /usr/local/PepAppsManager/
    '''
    config_data = read_config_file(CONFIG_PATH)
    config_data.append({
        "name": "Remove {}".format(d["label"]),
        "cmd": d["cmd"]
    })

    write_config_file(config_data, CONFIG_PATH)
    return json.dumps(config_data)


res = flusso_installazione(sys.argv[1])
print(urllib.parse.quote(res))