
default_desktop_text = r"""# -*- coding: UTF-8 -*-
[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=all/all;
Actions= default_action;
X-KDE-StartupNotify=false
X-KDE-Priority=TopLevel
X-KDE-Submenu=
Name=Name
Icon=kde
Exec=

[Desktop Action default_action]
X-KDE-Priority=TopLevel
X-KDE-Submenu=
Name=Name
Icon=kde
Exec=
"""


export_install_script= r"""#!/bin/bash
script_name=""
desktop_file=""
script_path=""

SELF=$(readlink -f "$0")
HERE=${SELF%/*}



if  [ "$script_name" != "" ]; then
SCRIPT_DIRECTORY=${script_path%/*}
relative_script_path=$(echo "$script_path" | cut -d'/' -f4-100)
mkdir -p "$SCRIPT_DIRECTORY"
cp "$HERE"/"$script_name" $HOME/"$relative_script_path"
chmod +x $HOME/"$relative_script_path"
fi


mkdir -p ~/.local/share/kservices5/ServiceMenus/
cp "$HERE"/"$desktop_file" $HOME/.local/share/kservices5/ServiceMenus/
kdialog --passivepopup Installed 2

echo -e "\n\n\nINSTALLED"

"""