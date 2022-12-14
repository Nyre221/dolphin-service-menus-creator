script_default_text = """#!/bin/bash

# Useful variables:
# $@ Contains the files you selected when you invoked the action
# $1 This contains only the first file
# $2 This contains only the second file
# $3 This contains only the third file
# . The dot means the folder in which you invoked the action

# If you want to use the command directly without the script I advise you to look here ( Under "The Exec key")
# https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html

# Mime-types are used to specify on what type of file the action should appear on.
# all/all; means that the action appears on everything.
# List: https://www.freeformatter.com/mime-types-list.html

# Script:

#If you want you can also run python scripts by writing #!/bin/python3 at the beginning of the script.

# Examples of what you can do with the script:

# Suggestions:
# Open dolphin in the terminal to check if the script works properly.
# any error messages will appear there.

# Warning:
# always use quotes "" when accessing a variable.
# if you don't do this you will have problems with files that contain spaces in the name

#### convert odt to pdf

##!/bin/bash
# for file in "$@" ; do
# libreoffice --headless --convert-to pdf "$file"
# done

# For the flatpak version of libreoffice the command should look like this:
# flatpak run --branch=stable --arch=x86_64 --command=libreoffice --file-forwarding org.libreoffice.LibreOffice --writer  --headless --convert-to pdf  "$file"




#### Create a symbolic link of the selected files

##!/bin/bash
# for file in "$@" ; do
# ln -s "$file"  ./"$(basename "$file")"-link
# done

"""

dictionary = dict(
    Name="Name",
    Command="This is not bash: Command %f",
    Submenu="Submenu Name",
    Mimetype="all/all;video/mp4;image/png",
    Script_text=script_default_text,
)