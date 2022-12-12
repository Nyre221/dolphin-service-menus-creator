#!/usr/bin/env python3

from PyQt5 import QtGui, QtWidgets, QtCore
import translation_manager
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
        self.current_action_row = 0

        # set the default text (after translation) for the plainTextEdit
        self.textedit_script.setPlainText(self.script_default_text)

        # set strings

        self.home_directory = os.path.expanduser("~")
        self.icons_themes_paths = list(glob.glob(f'/usr/share/icons/*'))
        self.icons_themes_paths.extend(list(glob.glob(f'{self.home_directory}/.local/share/icons/*')))
        self.kdeglobals_path = self.home_directory + "/.config/kdeglobals"
        self.editor_directory = self.home_directory + "/.config/dolphin_service_menus_creator"
        # directory to search for .desktop files
        self.servicemenus_locations = [self.home_directory + "/.local/share/kservices5/ServiceMenus/"]
        # append the NEW plasma service menus folder if exist
        if os.listdir(self.home_directory + "/.local/share/kio/servicemenus/"):
            self.servicemenus_locations.append(self.home_directory + "/.local/share/kio/servicemenus/")
        # a dictionary that contain the paths of the .desktop files.
        self.desktop_files_paths = {}
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
        os.makedirs(self.editor_directory, exist_ok=True)
        # create the old servicemenus directory if it doesn't exist.
        # I'm not creating both because on old plasma version it doesn't exist and the old still works on modern plasma.
        os.makedirs(self.servicemenus_locations[0], exist_ok=True)

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
        # clear the list and the dictionary because otherwise it will add two times the .desktop file when called as
        # an update function
        self.desktop_files_paths = {}
        self.listWidget_actions_list.clear()

        # add the elements to the actions list (gui) and to a dictionary for storing  name + path
        # this is needed because deleting the element is not reliable with an index list
        # qt seems to update the current row number after calling the signal item_selection_changed
        # this is necessary in first place because of the need of having to support two different service menus path
        for directory in self.servicemenus_locations:
            for file_name in os.listdir(directory):
                if file_name.endswith(".desktop"):
                    self.desktop_files_paths[file_name] = directory + file_name
                    self.listWidget_actions_list.addItem(file_name)

    def on_add_button_clicked(self):
        name = self.lineEdit_add_name.text().strip()
        if name == "":
            return
        filename = name + ".desktop"
        save_path = self.servicemenus_locations[0] + filename
        # check if the file already exist
        try:
            # save in the old plasma service menu folder for compatibility reasons [0]
            file = open(save_path, "xt")
            new_desktop_text = extra_text.default_desktop_text
            new_desktop_text = re.sub('^Name.*', f"Name={name}", new_desktop_text, flags=re.MULTILINE)
            file.write(new_desktop_text)
            file.close()
        except FileExistsError:
            self.label_desktopfile_already_exist_warning.show()
            return

        # appen the new file path to the dictionary
        self.desktop_files_paths[filename] = (save_path)
        # add and select the new action
        action = QtWidgets.QListWidgetItem(filename)
        self.listWidget_actions_list.addItem(action)
        self.listWidget_actions_list.setCurrentItem(action)

        self.lineEdit_add_name.clear()

    def save_data(self):
        file = open(self.path_to_desktop_file, "w")
        self.desktop_file_text = str(self.desktop_file_text)
        file.write(self.desktop_file_text)
        file.close()
        # workaround because the file directly altered with python don't work
        # on old version of dolphin or python probably due to a bug.
        # EXTRA:if I use open(path, w) instead of "wt" it seems to work,
        # but it's a bug that happens sometimes and I want to play it safe.
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

        # remove the action from the dictionary
        self.desktop_files_paths.pop(self.desktop_file_name)
        # remove the action from the menu and set the frame to disabled if there are no actions left
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
        # get current row and name of the action
        current_action = self.listWidget_actions_list.currentItem()
        # avoid crashing if there are no actions in the list
        if current_action == None:
            return
        self.desktop_file_name = current_action.text()
        # set the path to the desktop file and load the information
        self.path_to_desktop_file = self.desktop_files_paths[self.desktop_file_name]
        self.load_new_file_information()

    def load_new_file_information(self):
        self.create_script_on_save = False
        self.script_opened_externally = False
        self.button_open_script.setDisabled(True)

        # enable/re-enable the right frame after a selection at the beginning or after removing a file
        self.frame_right.setDisabled(False)

        # read the .desktop file text
        file = open(self.path_to_desktop_file, "r")
        self.desktop_file_text = file.read()
        file.close()

        #remove space at the beginning of every line
        self.desktop_file_text = re.sub("^ ","",self.desktop_file_text, flags=re.MULTILINE)

        # add the string for the submenu if it is missing from the .desktop
        self.desktop_file_text = self.add_submenu_and_priority(self.desktop_file_text)

        # extract the data from the .desktop file
        name_string = re.search('^Name.*', self.desktop_file_text, flags=re.MULTILINE)
        name = name_string.group(0).split("=", 1)[1]
        mime_type_string = re.search('^MimeType.*', self.desktop_file_text, flags=re.MULTILINE)
        mime_type = mime_type_string.group(0).split("=", 1)[1]
        command_string = re.search('^Exec.*', self.desktop_file_text, flags=re.MULTILINE)
        command = command_string.group(0).split("=", 1)[1]
        submenu_string = re.search('^X-KDE-Submenu.*', self.desktop_file_text, flags=re.MULTILINE)
        submenu = submenu_string.group(0).split("=", 1)[1]
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
        action_count = len(re.findall(f"^{re.escape('[')}Desktop Action", self.desktop_file_text, flags=re.MULTILINE))
        if action_count > 1:
            self.set_compatibility_button(True)
            self.label_incompatible_action_warning.show()
        else:
            # enable the button,editline, etc. if the file is compatible
            self.set_compatibility_button(False)

    def add_submenu_and_priority(self, text):
        # check if the submenu and X-KDE-Priority are written twice. some .desktops don't have the submenu string and
        # this prevents the program from modifying it. Also, if the submenu is not written under the correct section
        # [Desktop Entry] it doesn't work. I decided to write it everywhere to be safe. I'm not sure how older
        # versions of dolphin dealt with this (some things have changed now.)
        parameters_to_add = []
        # X-KDE-Priority is needed because otherwise the sub-menu doesn't work. in older versions of dolphin it was
        # used to keep the newly created action out of the dolphin actions submenu (the general one) and keep it on
        # top, but now it just creates two submenus with the same name in the context menu.
        for parameter in ["X-KDE-Priority", "X-KDE-Submenu"]:
            if len(re.findall(f"^{parameter}", text, flags=re.MULTILINE)) < 2:
                parameters_to_add.append(parameter)

        # use the same submenu name if the string exists at least once
        submenu_original_string = re.findall(f"^X-KDE-Submenu.*", text, flags=re.MULTILINE)
        if len(submenu_original_string) > 0:  # check if already exist but not
            submenu_string = submenu_original_string[0]
        else:
            submenu_string = "X-KDE-Submenu="

        new_text = ""
        if not parameters_to_add == []:
            for line in text.splitlines(keepends=True):
                new_text += line
                # add the missing parameters under any string starting with [Desktop
                if line.strip().startswith("[Desktop"):
                    for parameter in parameters_to_add:
                        if "Priority" in parameter:
                            new_text += f"{parameter}=TopLevel\n"
                        elif "Submenu" in parameter:
                            new_text += f"{submenu_string}\n"
            text = new_text
        return text

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

    def set_icon_preview(self):
        # get the string relative to the icon in the .desktop file
        icon_string = re.search('^Icon.*', self.desktop_file_text, flags=re.MULTILINE)
        # get the name of the icon
        icon = icon_string.group(0).split("=", 1)[1]
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
    # NOTA: using lambda x: is the only way I found to avoid processing escape characters while using re.sub()
    def set_new_name(self):
        name = self.lineEdit_name.text()
        self.desktop_file_text = re.sub('^Name.*', lambda x: f"Name={name}", self.desktop_file_text, flags=re.MULTILINE)
        self.show_save_warning()

    def set_new_submenu(self):
        sumbmenu_name = self.lineEdit_submenu.text()
        self.desktop_file_text = re.sub('^X-KDE-Submenu.*', lambda x: f"X-KDE-Submenu={sumbmenu_name}",
                                        self.desktop_file_text, flags=re.MULTILINE)
        self.show_save_warning()

    def set_new_command(self):
        command_name = self.lineEdit_command.text()
        self.desktop_file_text = re.sub('^Exec.*', lambda x: f"Exec={command_name}", self.desktop_file_text,
                                        flags=re.MULTILINE)
        self.show_save_warning()

    def set_new_mimetype(self):
        mimetype_name = self.lineEdit_mimetype.text()
        self.desktop_file_text = re.sub('^MimeType.*', lambda x: f"MimeType={mimetype_name}", self.desktop_file_text,
                                        flags=re.MULTILINE)
        self.show_save_warning()

    def set_new_icon(self, icon_name):
        self.desktop_file_text = re.sub('^Icon.*', lambda x: f"Icon={icon_name}", self.desktop_file_text,
                                        flags=re.MULTILINE)
        self.set_icon_preview()
        self.show_save_warning()

    def show_save_warning(self):
        self.label_save_before_exit.show()

    def script_edited(self):
        self.label_save_before_exit.show()
        if not self.script_attached:
            self.label_unused_script_warning.show()

    def load_translation(self, Form):
        translator = translation_manager.Translator()
        qt_translation = translator.get_qt_translation()
        # load the qt translation if it is available.
        if qt_translation is not None:
            self.trans = QtCore.QTranslator()
            self.trans.loadFromData(qt_translation)
            QtWidgets.QApplication.instance().installTranslator(self.trans)
            self.retranslateUi(Form)
        # translate the placeholder strings
        # QtDesigner doesn't save them for some reason, and so I'm adding/translating them separately.
        self.lineEdit_add_name.setPlaceholderText(translator.translate("Name"))
        self.lineEdit_name.setPlaceholderText(translator.translate("Name"))
        self.lineEdit_submenu.setPlaceholderText(translator.translate("Submenu"))
        self.lineEdit_command.setPlaceholderText(translator.translate("Command"))
        self.lineEdit_mimetype.setPlaceholderText(translator.translate("Mimetype"))
        self.script_default_text = translator.translate("Script_text")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Main(Form)
    Form.show()
    sys.exit(app.exec_())
