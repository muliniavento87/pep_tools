#!/bin/sh

# Recupera il percorso assoluto dello script corrente
SCRIPT=$(readlink -f "$0")
# Recupera la directory contenente lo script corrente
SCRIPTPATH=$(dirname "$SCRIPT")
# Path setup
PATH_SETUP="${SCRIPTPATH}/setup_data"
# Home user loggato (NON da niente se non hai avviato lo script con SUDO)
USER_HOME="/home/${USER}"
HOME="/home/${SUDO_USER}"

if [ -z ${SUDO_USER} ]; then
    #echo "Sembra che il comando non sia stato avviato con sudo, uso home user loggato a sistema '${USER_HOME}'";
    HOME=${USER_HOME};
    echo "Avviare lo script con SUDO"
    exit 0;
fi

# app pep_app_manager
exist=$(which peplinks);
if [ -z ${exist} ]; then
    echo "Installo peplinks ..."
    # creo cartella
    v0="cp -r ${PATH_SETUP}/peplinks /usr/local/PepAppsLinks/";
    # link globale
    v1="ln -s /usr/local/PepAppsLinks/start.sh /usr/local/bin/peplinks";
    # link menu
    v2="cp ${PATH_SETUP}/peplinks/applet-peplinks.desktop /usr/share/applications/applet-peplinks.desktop";
    # autostart
    v3="cp ${PATH_SETUP}/peplinks/applet-peplinks.desktop ${HOME}/.config/autostart/applet-peplinks.desktop";
    # set permessi utente per file configurazioni
    v4="chmod 777 /usr/local/PepAppsLinks/store.json";
    # Messaggio di avviso OK
    v5="echo 'OK peplinks installato'"

    ${v0} && ${v1} && ${v2} && ${v3} && ${v4} && ${v5};
fi

# dipendenza sudogui
exist=$(which sudogui);
if [ -z ${exist} ]; then
    echo "Installo sudogui ..."
    # creo cartella
    v0="cp -r ${PATH_SETUP}/sudogui /usr/local/PepAppsSudogui/";
    # link globale
    v1="ln -s /usr/local/PepAppsSudogui/sudogui.sh /usr/local/bin/sudogui";
    # Messaggio di avviso OK
    v2="echo 'OK sudogui installato'"

    ${v0} && ${v1} && ${v2};
fi

echo "Installazione terminata"