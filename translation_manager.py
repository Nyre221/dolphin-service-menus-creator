import importlib.resources
import translations.qt_translations
from translations.qt_translations import available_qt_translations
from translations.placeholder_translations import available_placeholder_translations
import locale
import os

class Translator:

    def __init__(self):
        self.system_language = os.getenv("LANG").split(".")[0]

    def translate(self, string: str):
        # get the dictionary of the current locale if exist or return the default one otherwise
        locale_dictionary = available_placeholder_translations.get(self.system_language, available_placeholder_translations["en_US"])
        # return the translated string or the default one in case the string doesn't exist.
        translated_string = locale_dictionary.get(string, available_placeholder_translations["en_US"][string])
        return translated_string



    def get_qt_translation(self):
        # since there are two translation systems, unfortunately I have to manage qt separately.
            # check if the translation file for the current locale exists
        if available_qt_translations.get(self.system_language,None) != None:
            # load the translation from a package. Needed because if the program is zipped with zipapp
            # the translation cannot be loaded in the normal way.
            translation = importlib.resources.read_binary(translations.qt_translations,available_qt_translations[self.system_language])
            return translation
        else:
            # because the english words are hardcoded, there is not a translation file to return.
            return None

