import importlib.resources
import translations
from translations.placeholder_translations import available_placeholder_translations
import locale

available_qt_translation = ["it_IT", "nl_NL"]


class Translator:

    def __init__(self):
        self.system_locale = locale.getlocale()[0]


    def translate(self, string: str):
        # get the dictionary of the current locale if exist or return the default one otherwise
        locale_dictionary = available_placeholder_translations.get(self.system_locale, available_placeholder_translations["en_US"])
        # return the translated string or the default one in case the string doesn't exist.
        translated_string = locale_dictionary.get(string, available_placeholder_translations["en_US"][string])
        return translated_string



    def get_qt_translation(self):
        # since there are two translation systems, unfortunately I have to manage qt separately.
            # check if the translation file for the current locale exists
        # if available_qt_translation.get(self.system_locale, None) != None:
        if self.system_locale in available_qt_translation:
            # load the translation from a package. Needed because if the program is zipped with zipapp
            # the translation cannot be loaded in the normal way.
            translation = importlib.resources.read_binary(translations, self.system_locale + ".qm")
            return translation
        else:
            # because the english words are hardcoded, there is not a translation file to return.
            return None

