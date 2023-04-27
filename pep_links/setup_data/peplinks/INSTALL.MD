## crea cartella con i files
/usr/local/PepAppsManager/apps/PepLinks/

## crea link (OS cmd)
sudo ln -s /usr/local/PepAppsManager/apps/PepLinks/start.sh /usr/local/bin/peplinks

## autorun (copio .desktop in ~/.config/autostart/)
cp /usr/local/PepAppsManager/applet-peplinks.desktop ~/.config/autostart/
