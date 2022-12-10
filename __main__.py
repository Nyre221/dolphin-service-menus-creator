#!/usr/bin/env python3

import importlib.resources
from PyQt5 import QtGui, QtWidgets, QtCore

import translations
from translations import extra_translations
from translations.extra_translations import placeholder_translations
from ui_dolphin_service_menus_creator import Ui_Form
import os
import sys
import re
import subprocess
import extra_text
import shutil
import glob


class Main(Ui_Form):

    def __init__(self, Form):

        super(Main, self).setupUi(Form)
        self.program_location = os.path.realpath(os.path.dirname(__file__))
        self.system_locale = os.getenv('LANG')
        self.load_translation(Form)

        # hide the kdialog warning if it is installed in the system
        response = subprocess.call(['which', 'kdialog'], stdout=subprocess.PIPE)
        if response == 0:
            self.kdialog_installed = True
            self.label_kdialog_missing_warning.hide()
        else:
            self.kdialog_installed = False

        # set variables
        self.create_script_on_save = False
        self.script_attached = False
        self.script_opened_externally = False

        # set the default text (after translation) for the plainTextEdit
        self.textedit_script.setPlainText(self.script_default_text)

        # set strings
        self.home_directory = os.path.expanduser("~")
        self.icons_themes_paths = list(glob.glob(f'/usr/share/icons/*'))
        self.icons_themes_paths.extend(list(glob.glob(f'{self.home_directory}/.local/share/icons/*')))
        self.kdeglobals_path = self.home_directory + "/.config/kdeglobals"
        self.editor_directory = self.home_directory + "/.config/dolphin_service_menus_creator"
        self.service_menu_directory = self.home_directory + "/.local/share/kservices5/ServiceMenus/"
        self.path_to_desktop_file = ""
        self.desktop_file_text: str = ""
        self.current_script_path = ""
        self.desktop_file_name = ""



        # hide the unnecessary label
        self.label_save_before_exit.hide()
        self.label_unused_script_warning.hide()
        self.label_incompatible_action_warning.hide()
        self.label_desktopfile_already_exist_warning.hide()
        self.label_export_warning.hide()
        self.connect_signal()

        # the frame is disabled because no .desktop is loaded/selected
        self.frame_right.setDisabled(True)

        # create the required folders (first run)
        os.makedirs(self.service_menu_directory, exist_ok=True)
        os.makedirs(self.editor_directory, exist_ok=True)



        self.load_desktop_files()

    def connect_signal(self):
        self.button_add.clicked.connect(self.on_add_button_clicked)
        self.listWidget_actions_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.button_icon.clicked.connect(self.on_icon_button_clicked)
        self.button_save.clicked.connect(self.save_data)
        self.button_remove.clicked.connect(self.remove_desktop_file)
        self.button_use_script.clicked.connect(self.use_script)
        self.button_open_script.clicked.connect(self.open_script)
        self.button_mimetype.clicked.connect(self.detect_mimetype)
        self.button_export.clicked.connect(self.export_action)
        self.lineEdit_name.textEdited.connect(self.set_new_name)
        self.lineEdit_add_name.returnPressed.connect(self.on_add_button_clicked)
        self.lineEdit_submenu.textEdited.connect(self.set_new_submenu)
        self.lineEdit_mimetype.textChanged.connect(self.set_new_mimetype)
        self.lineEdit_command.textChanged.connect(self.set_new_command)
        self.textedit_script.textChanged.connect(self.script_edited)

    def load_desktop_files(self):
        # clear the list because otherwise it will add two times the .desktop file when called as an update function
        self.listWidget_actions_list.clear()

        for x in os.listdir(self.service_menu_directory):
            if x.endswith(".desktop"):
                self.listWidget_actions_list.addItem(x)

    def on_add_button_clicked(self):

        name = self.lineEdit_add_name.text().strip()
        if name == "":
            return
        filename = name + ".desktop"
        # check if the file already exist
        try:
            file = open(self.service_menu_directory + filename, "xt")
            new_desktop_text = extra_text.default_desktop_text
            new_desktop_text = re.sub('^Name.*', f"Name={name}", new_desktop_text, flags=re.MULTILINE)
            file.write(new_desktop_text)
            file.close()
        except FileExistsError:
            self.label_desktopfile_already_exist_warning.show()
            return

        # add and select the new item
        item = QtWidgets.QListWidgetItem(filename)
        self.listWidget_actions_list.addItem(item)
        self.listWidget_actions_list.setCurrentItem(item)

        self.lineEdit_add_name.clear()

    def save_data(self):
        file = open(self.path_to_desktop_file, "w")
        self.desktop_file_text = str(self.desktop_file_text)
        file.write(self.desktop_file_text)
        file.close()
        # workaround because the file directly altered with python don't work
        # on old version of dolphin or python probably due to a bug.
        # EXTRA:if I use open(path, w) instead of "wt" it seems to work,
        # but it's a bug that happens sometimes and I want to play it safe
        # Reopen the file and save it again.
        subprocess.run(["bash", "-c", f"sed -i 's/ / /' '{self.path_to_desktop_file}'"])

        if self.create_script_on_save:
            self.create_script()

        self.save_script()
        self.label_save_before_exit.hide()

    def save_script(self):
        if self.script_attached and not self.script_opened_externally:
            file = open(self.current_script_path, "wt")
            file.write(self.textedit_script.toPlainText())
            file.close()

    def remove_desktop_file(self):
        # remove the script and .desktop file
        if os.path.isfile(self.path_to_desktop_file):
            os.remove(self.path_to_desktop_file)
        if self.script_attached and not self.create_script_on_save and os.path.isfile(self.current_script_path):
            os.remove(self.current_script_path)

        # remove the action from the menu and set the frame to disabled if there are no items left
        self.listWidget_actions_list.takeItem(
            self.listWidget_actions_list.row(self.listWidget_actions_list.currentItem()))
        if self.listWidget_actions_list.count() == 0:
            self.frame_right.setDisabled(True)

    def export_action(self):
        if not self.kdialog_installed:
            return
        if not os.path.exists(self.path_to_desktop_file):
            return
        # ask the user to select the folder
        # self.home_directory tell to kdialog what folder need to show/expand first
        result = subprocess.run(["kdialog", "--getexistingdirectory", self.home_directory], stdout=subprocess.PIPE,
                                text=True)
        if result.returncode != 0:
            return

        if result.stdout.strip("\n") == "/home":
            self.label_export_warning.show()
            return
        else:
            self.label_export_warning.hide()
        # I want all the files to be copied inside another directory with the name of the .desktop file
        directory = result.stdout.strip("\n") + "/" + os.path.splitext(self.desktop_file_name)[0] + "-dolphin_action"

        # check if the directory exist
        if not os.path.isdir(directory):
            os.makedirs(directory)

        # Prepare the re-installation script
        install_script = extra_text.export_install_script

        # make a copy of the desktop file
        desktop_file_output = f"{directory}/{self.desktop_file_name}"
        # remove the file if already exist
        if os.path.isfile(desktop_file_output):
            os.remove(desktop_file_output)
        shutil.copy(self.path_to_desktop_file, desktop_file_output)
        # set the name of the desktop file in the installation script
        install_script = re.sub("^desktop_file=.*", f"desktop_file='{self.desktop_file_name}'", install_script,
                                flags=re.MULTILINE)

        # make a copy of the script
        if self.script_attached and not self.create_script_on_save and os.path.exists(self.current_script_path):
            script_name = os.path.basename(self.current_script_path)
            script_file_output = f"{directory}/{script_name}"
            # remove the file if already exist
            if os.path.isfile(script_file_output):
                os.remove(script_file_output)
            shutil.copy(self.current_script_path, script_file_output)
            install_script = re.sub("^script_name=.*", f"script_name='{script_name}'", install_script,
                                    flags=re.MULTILINE)
            install_script = re.sub("^script_path=.*", f"script_path='{self.current_script_path}'", install_script,
                                    flags=re.MULTILINE)

        # create the installation script file
        install_script_file_output = directory + "/INSTALL.sh"
        file = open(install_script_file_output, "w")
        file.write(install_script)
        file.close()
        subprocess.run(["chmod", "+x", install_script_file_output])

    def on_icon_button_clicked(self):
        if not self.kdialog_installed:
            return
        result = subprocess.run(["kdialog", "--geticon"], stdout=subprocess.PIPE, text=True)
        if result.returncode == 0:
            self.set_new_icon(result.stdout.strip("\n"))

    def on_item_selection_changed(self):
        current_item = self.listWidget_actions_list.currentItem()
        if current_item == None:
            return

        current_item_text = current_item.text()

        self.desktop_file_name = current_item_text
        self.path_to_desktop_file = self.service_menu_directory + self.desktop_file_name
        self.load_new_file_information()

    def load_new_file_information(self):

        self.script_opened_externally = False
        self.button_open_script.setDisabled(True)

        # enable/re-enable the right frame after a selection at the beginning or after removing a file
        self.frame_right.setDisabled(False)

        # read the .desktop file text
        file = open(self.path_to_desktop_file, "r")
        self.desktop_file_text = file.read()
        file.close()

        # extract the data from the .desktop file
        name_string = re.search('^Name.*', self.desktop_file_text, flags=re.MULTILINE)
        name = name_string.group(0).split("=")[1]
        mime_type_string = re.search('^MimeType.*', self.desktop_file_text, flags=re.MULTILINE)
        mime_type = mime_type_string.group(0).split("=")[1]
        submenu_string = re.search('^X-KDE-Submenu.*', self.desktop_file_text, flags=re.MULTILINE)
        submenu = submenu_string.group(0).split("=")[1]
        command_string = re.search('^Exec.*', self.desktop_file_text, flags=re.MULTILINE)
        command = command_string.group(0).split("=")[1]
        # this is needed to get the icon preview because the string name is not enough
        self.set_icon_preview()

        # check if there is a script attached
        current_script = re.search('#attached_script=.*', self.desktop_file_text)
        if current_script == None:
            self.textedit_script.setPlainText(self.script_default_text)
            self.script_attached = False
            self.current_script_path = ""
        else:
            self.script_attached = True
            self.current_script_path = current_script.group(0).split("=")[1]
            script_file = open(self.current_script_path, "rt")
            script_text = script_file.read()
            script_file.close()
            self.textedit_script.setPlainText(script_text)
            self.button_open_script.setDisabled(False)

        # set the information to the ui (except for the icon)
        self.lineEdit_name.setText(name)
        self.lineEdit_mimetype.setText(mime_type)
        self.lineEdit_submenu.setText(submenu)
        self.lineEdit_command.setText(command)
        # reset the label to their default state
        self.label_save_before_exit.hide()
        self.label_unused_script_warning.hide()
        self.label_incompatible_action_warning.hide()
        self.label_desktopfile_already_exist_warning.hide()
        self.label_export_warning.hide()
        # check if the desktop file have more than one action and disable the frame if this is the case
        # multi actions per file not implemented (compatibility)
        action_count = len(re.findall(re.escape('[Desktop Action'), self.desktop_file_text))
        if action_count > 1:
            self.set_compatibility_button(True)
            self.label_incompatible_action_warning.show()
        else:
            # enable the button,editline, etc. if the file is compatible
            self.set_compatibility_button(False)

    def set_compatibility_button(self, disable=True):
        # disabled the button/linEdit, etc. if the file is incompatible
        self.button_icon.setDisabled(disable)
        self.button_save.setDisabled(disable)
        self.button_use_script.setDisabled(disable)
        self.button_mimetype.setDisabled(disable)

        self.lineEdit_name.setDisabled(disable)
        self.lineEdit_command.setDisabled(disable)
        self.lineEdit_mimetype.setDisabled(disable)
        self.lineEdit_submenu.setDisabled(disable)
        self.textedit_script.setDisabled(disable)
        # this button must remain disabled if the script is not attached
        if self.script_attached and not disable:
            self.button_open_script.setDisabled(False)
        else:
            self.button_open_script.setDisabled(True)

    def use_script(self):
        self.label_unused_script_warning.hide()
        if self.script_attached == False:
            self.script_attached = True
            # set the new script path and name
            script_name = self.desktop_file_name.split(".desktop")[0]
            self.current_script_path = f'{self.editor_directory}/script_{script_name}'
            # append the script path in the .desktop file
            self.desktop_file_text += f"#attached_script={self.current_script_path}"
            # this is done to create the script only if the user press the save button
            self.create_script_on_save = True

        # setting the new string in the lineEdit and should trigger the text_changed signal
        self.lineEdit_command.setText(f"'{self.current_script_path}' %F")

    def create_script(self):
        # try to create the script if it doesn't already exist
        try:

            script_file = open(self.current_script_path, "wt")
            script_file.close()
            subprocess.run(["chmod", "+x", self.current_script_path])
            self.create_script_on_save = False
        except FileExistsError:
            print("script exist")

        self.button_open_script.setDisabled(False)

    def open_script(self):
        self.save_script()
        self.script_opened_externally = True
        self.textedit_script.setDisabled(True)
        subprocess.run(["xdg-open", self.current_script_path])

    def detect_mimetype(self):
        if not self.kdialog_installed:
            return
        result = subprocess.run(["kdialog", "--getopenfilename"], stdout=subprocess.PIPE, text=True)

        if result.returncode == 0:
            # get the mimetype from the selected file
            mimetype = subprocess.run(["xdg-mime", "query", "filetype", result.stdout.strip("\n")],
                                      stdout=subprocess.PIPE, text=True)
            mimetype = mimetype.stdout.strip("\n")
            original_mimetype = self.lineEdit_mimetype.text()

            new_mimetype_string = ""
            # remove the all/all mimetype if present and add ";" at the end if missing
            if "all/all" in original_mimetype:
                original_mimetype = ""
            elif not original_mimetype.endswith(";") and len(original_mimetype.replace(" ", "")) > 1:
                new_mimetype_string = ";"

            new_mimetype_string += f"{original_mimetype}{new_mimetype_string}{mimetype};"
            # setting the new string in the lineEdit and should trigger the text_changed signal
            self.lineEdit_mimetype.setText(new_mimetype_string)

    def set_new_icon(self, icon_name):
        self.desktop_file_text = re.sub('^Icon.*', f"Icon={icon_name}", self.desktop_file_text, flags=re.MULTILINE)
        self.set_icon_preview()
        self.show_save_warning()

    def set_icon_preview(self):
        # get the string relative to the icon in the .desktop file
        icon_string = re.search('^Icon.*', self.desktop_file_text, flags=re.MULTILINE)
        # get the name of the icon
        icon = icon_string.group(0).split("=")[1]
        # use directly the icon name if it is a valid path (when selected a local file from kdialog)
        if os.path.isabs(icon):
            icon_path = icon
        else:
            icon_path = self.search_icon(icon)

        if icon_path == "":
            return

        # set the icon of the button
        q_icon = QtGui.QIcon()
        q_icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button_icon.setIcon(q_icon)

    def search_icon(self, icon):
        # from kdeglobals extract the name of the icon theme in use
        file = open(self.kdeglobals_path, "r")
        text = file.read()
        file.close()

        # search for the string
        icons_theme_name = re.findall('Theme=.*', text)
        # on some distro the string is not present and because  of this I have added a check
        # The variable is set to breeze if no string is found
        if len(icons_theme_name) == 1:
            icons_theme_name = icons_theme_name[0].split("=")[1]

        else:
            icons_theme_name = "breeze"

        # plasma seems to check for icons in this order: user icons theme -> plasma default icons -> hicolor
        theme_to_check = [icons_theme_name]
        # this is done because some icons are stored with just part of the name
        # this block try to avoid searching two times in the same theme folder
        if len(re.findall("-", icons_theme_name)) > 0:
            icons_theme_half_name = icons_theme_name.split("-")[0]
            theme_to_check.append(icons_theme_half_name)
        if not "breeze" in icons_theme_name:
            theme_to_check.append("breeze")

        theme_to_check.append("hicolor")
        # search the icon
        for theme in theme_to_check:
            for theme_path in self.icons_themes_paths:
                theme_folder_name = os.path.basename(theme_path)
                if theme == theme_folder_name:
                    icons_paths = list(glob.glob(f'{theme_path}/**/*.*', recursive=True))
                    # the list is inverted because this is an easy way to make it find the largest resolution first (works ok..)
                    icons_paths.reverse()
                    for path in icons_paths:
                        path = str(path)
                        # get the name of the image and remove the extension
                        image_name = os.path.splitext(os.path.basename(path))[0]
                        # if
                        if icon == image_name:
                            icon_path = path
                            return icon_path
        # if the function can't find the icon return an empty string
        return ""

    # even if not ideal, I decided to connect the signal "pressed" of every button to update the information on the
    # .desktopfile (not save to file) instead of retrieving the data when the save button is pressed. I have done
    # this because I think it can be more flexible (but less maintainable) and necessary for the icon because there
    # is no text to retrieve normally and I need the signal for the save waring message in any case
    def set_new_name(self):
        name = self.lineEdit_name.text()
        self.desktop_file_text = re.sub('^Name.*', f"Name={name}", self.desktop_file_text, flags=re.MULTILINE)
        self.show_save_warning()

    def set_new_submenu(self):
        sumbmenu_name = self.lineEdit_submenu.text()
        self.desktop_file_text = re.sub('^X-KDE-Submenu.*', f"X-KDE-Submenu={sumbmenu_name}", self.desktop_file_text,
                                        flags=re.MULTILINE)
        self.show_save_warning()

    def set_new_command(self):
        command_name = self.lineEdit_command.text()
        self.desktop_file_text = re.sub('^Exec.*', f"Exec={command_name}", self.desktop_file_text, flags=re.MULTILINE)
        self.show_save_warning()

    def set_new_mimetype(self):
        mimetype_name = self.lineEdit_mimetype.text()
        self.desktop_file_text = re.sub('^MimeType.*', f"MimeType={mimetype_name}", self.desktop_file_text,
                                        flags=re.MULTILINE)
        self.show_save_warning()

    def show_save_warning(self):
        self.label_save_before_exit.show()

    def script_edited(self):
        self.label_save_before_exit.show()
        if not self.script_attached:
            self.label_unused_script_warning.show()

    def load_translation(self, Form):
        locale_key = "en"
        if "it_IT" in self.system_locale:
            locale_key = "it"
            self.trans = QtCore.QTranslator()
            # load the translation from a package. needed because if the program is zipped with zipapp
            # the translation cannot be loaded with load("path/to/file/name")
            translation = importlib.resources.read_binary(translations, "eng-it.qm")
            self.trans.loadFromData(translation)
            QtWidgets.QApplication.instance().installTranslator(self.trans)
            self.retranslateUi(Form)

        # Qtdesigner don't set the placeholder text for some reason and I want to add a script default text
        self.set_extra_text(locale_key)

    def set_extra_text(self,locale_key):
        # very dirty way but it is enough
        name_placeholder_text = placeholder_translations[locale_key].get("Name", placeholder_translations["en"]["Name"])
        command_placeholder_text = placeholder_translations[locale_key].get("Command",
                                                                        placeholder_translations["en"]["Command"])
        mimetype_placeholder_text = placeholder_translations[locale_key].get("Mimetype",
                                                                         placeholder_translations["en"]["Mimetype"])
        submenu_placeholder_text = placeholder_translations[locale_key].get("Submenu",
                                                                        placeholder_translations["en"]["Submenu"])
        # this is the default text of the script
        # I'm translating it because I want to add useful information in it
        self.script_default_text = extra_translations.script_default_text_dict.get(locale_key,extra_translations.script_default_text_dict["en"])

        self.lineEdit_add_name.setPlaceholderText(name_placeholder_text)
        self.lineEdit_name.setPlaceholderText(name_placeholder_text)
        self.lineEdit_submenu.setPlaceholderText(submenu_placeholder_text)
        self.lineEdit_command.setPlaceholderText(command_placeholder_text)
        self.lineEdit_mimetype.setPlaceholderText(mimetype_placeholder_text)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Main(Form)
    Form.show()
    sys.exit(app.exec_())