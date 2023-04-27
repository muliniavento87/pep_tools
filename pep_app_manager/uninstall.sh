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
exist=$(which pepapps);
if [ -n ${exist} ]; then
    echo "Rimozione pepapps ..."
    # rimozione .desktop
    v0="rm /usr/share/applications/applet-pepapps.desktop"
    v1="rm ${HOME}/.config/autostart/applet-pepapps.desktop"
    # rimozione link globale
    v2="rm /usr/local/bin/pepapps"
    # rimozione cartella
    v3="rm -r /usr/local/PepAppsManager/"
    # Messaggio di avviso OK
    v4="echo 'OK pepapps rimosso'"

    ${v0} ; ${v1} ; ${v2} ; ${v3} ; ${v4};
fi

# dipendenza sudogui
exist=$(which sudogui);
if [ -n ${exist} ]; then
    echo "Rimozione sudogui ..."
    # rimozione link globale
    v0="rm /usr/local/bin/sudogui"
    # rimozione cartella
    v1="rm -r /usr/local/PepAppsSudogui/"
    # Messaggio di avviso OK
    v2="echo 'OK sudogui rimosso'"

    ${v0} ; ${v1} ; ${v2};
fi

echo "Disinstallazione terminata"