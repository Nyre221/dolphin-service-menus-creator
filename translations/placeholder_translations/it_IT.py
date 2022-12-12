script_default_text = """#!/bin/bash

#Variabili utili:
#$@ Contiene i file che hai selezionato quando hai invocato l'azione
#$1 Questa contiene solo il primo file
#$2 Questa contiene solo il secondo file
#$3 Questa contiene solo il terzo file
# . Il punto Indica la cartella nella quale hai invocato l'azione

# Se vuoi usare direttamente il comando senza lo script ti consiglio a di guardare qui (Sotto a "The Exec key" )
# https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html

# I mime-type servono per specificare su quale tipo di file l'azione deve comparire.
# all/all; significa che deve compari su tutto. 
# Lista: https://www.freeformatter.com/mime-types-list.html

# Script:

# Se vuoi puoi anche eseguire script in python scrivendo #!/bin/python3 all'inizio dello script.  

# Esempi di cosa puoi fare con lo script:

# Suggerimento:
# Apri dolphin tramite il terminale per verificare se lo script funziona correttamente.
# ogni messaggio di errore comparira lì. 

# Avvertimento:
# Metti sempre le virgolette "" quando accedi ad una variabile. 
# se non lo fai avrai problemi con i file che contengono degli spazi nel nome



#### converte gli odt in pdf

##!/bin/bash
# for file in "$@" ; do
# libreoffice --headless --convert-to pdf "$file"
# done

#per libreoffice versione flatpak il comando dovrebbe essere simile a questo:
# flatpak run --branch=stable --arch=x86_64 --command=libreoffice --file-forwarding org.libreoffice.LibreOffice --writer  --headless --convert-to pdf  "$file"




#### Crea un collegamento simbolico dei file selezionati

##!/bin/bash
# for file in "$@" ; do
# ln -s "$file"  ./"$(basename "$file")"-link
# done
"""


dictionary = dict(
        Name="Nome",
        Command="Questo non è bash: Comando %f",
        Submenu="Nome Sottomenu",
        Mimetype="all/all;video/mp4;image/png",
        Script_text=script_default_text,
    )