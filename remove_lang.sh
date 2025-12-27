#!/bin/bash

# Script to remove a language code from the LANG variable in .env file

# Check if argument is provided
if [ $# -ne 1 ]; then
    echo "Error: Please provide a two-letter language code as an argument"
    exit 1
fi

arg="$1"

# Validate the argument (2 letters of Latin alphabet)
if [[ ! "$arg" =~ ^[a-zA-Z]{2}$ ]]; then
    echo "Error: Argument must be a two-letter Latin alphabet code"
    exit 1
fi

# Convert to lowercase
lang_code=$(echo "$arg" | tr '[:upper:]' '[:lower:]')

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file does not exist"
    exit 1
fi

# Read the .env file and find the LANG line
lang_line=$(grep "^LANG=" .env)
if [ -z "$lang_line" ]; then
    echo "Error: LANG variable not found in .env file"
    exit 1
fi

# Extract the current value after LANG=
current_value="${lang_line#LANG=}"

# Check if the language code exists in the value
if [[ ",$current_value," == *",$lang_code,"* ]]; then
    # Remove the language code
    # First, replace "code," with nothing if it's in the middle
    new_value=$(echo "$current_value" | sed "s/$lang_code,//g")
    # Then, remove ",code" if it's at the end
    new_value=$(echo "$new_value" | sed "s/,$lang_code$//g")
    # Finally, remove "code" if it's the only value
    if [ "$new_value" = "$lang_code" ]; then
        new_value=""
    fi
    
    # Clean up double commas to single comma
    new_value=$(echo "$new_value" | sed 's/,,/,/g')
    # Remove leading comma if present
    new_value=$(echo "$new_value" | sed 's/^,//')
    # Remove trailing comma if present
    new_value=$(echo "$new_value" | sed 's/,$//')
    
    # Replace the line in the file
    sed -i '' "s/^LANGS=.*/LANGS=$new_value/" .env
    
    echo "Successfully removed '$lang_code' from LANGS variable"
else
    echo "Language code '$lang_code' does not exist in LANGS variable"
fi