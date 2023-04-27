#! /bin/sh
eval "export SUDO_ASKPASS=/usr/local/PepAppsSudogui/./askpass.sh" && eval "sudo -A $@"
