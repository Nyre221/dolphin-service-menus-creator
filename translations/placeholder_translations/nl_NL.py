script_default_text = """#!/bin/bash

# Handige variabelen:
# $@ bevat de geselecteerde bestanden ten tijde van de actie
# $1 bevat alleen het eerste bestand
# $2 bevat alleen het tweede bestand
# $3 bevat alleen het derde bestand
# . de punt staat voor de map waarin de actie wordt uitgevoerd

# Als je een opdracht direct wilt gebruiken, dus zonder script, kijk dan op
# https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html (het onderwerp betreffende de ‘Exec’-sleutel)

# Mimetypes worden gebruikt om aan te geven op welk soort bestanden een actie dient te worden uitgevoerd.
# all/all; = uitvoeren op alle bestandstypes.
# Volledige lijst: https://www.freeformatter.com/mime-types-list.html

# Script:

#Je kunt, desgewenst, pythonscripts uitvoeren door een script te beginnen met #!/bin/python3

# Scriptvoorbeelden:

# Suggesties:
# Open Dolphin in een terminalvenster om te controleren of een script naar behoren werkt..
# Foutmeldingen worden daar ook getoond.

# Waarschuwing:
# gebruik altijd dubbele aanhalingstekens "" rondom een variabel,
# anders kunnen er problemen optreden met bestandsnamen die spaties bevatten

#### Converteer odt naar pdf

##!/bin/bash
# for file in "$@" ; do
# libreoffice --headless --convert-to pdf "$file"
# done

# De opdracht voor de flatpakversie van LibreOffice dient als volgt te worden opgemaakt:
# flatpak run --branch=stable --arch=x86_64 --command=libreoffice --file-forwarding org.libreoffice.LibreOffice --writer  --headless --convert-to pdf  "$file"




#### Maak een snelkoppeling naar de geselecteerde bestanden

##!/bin/bash
# for file in "$@" ; do
# ln -s "$file"  ./"$(basename "$file")"-link
# done

"""

dictionary = dict(
    Name="Naam",
    Command="Dit is geen bash: opdracht %f",
    Submenu="Naam van onderliggend menu",
    Mimetype="all/all;video/mp4;image/png",
    Script_text=script_default_text,
)
