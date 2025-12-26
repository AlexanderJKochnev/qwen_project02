#!/usr/bin/env python3
"""
Script to add language codes to .env file
"""
import re
from pathlib import Path

def add_language_to_env(lang_codes: list):
    """Add language codes to the LANGS variable in .env file"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print(f"Error: {env_file} does not exist")
        return False
    
    content = env_file.read_text()
    
    # Find the LANGS line and update it
    pattern = r'^(LANGS=.*)$'
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.startswith('LANGS='):
            current_langs = line.split('=')[1]  # Get current languages
            current_lang_list = [lang.strip() for lang in current_langs.split(',')]
            
            # Add new languages if they're not already present
            for lang in lang_codes:
                if lang not in current_lang_list:
                    current_lang_list.append(lang)
            
            new_langs = ','.join(current_lang_list)
            lines[i] = f'LANGS={new_langs}'
            break
    
    new_content = '\n'.join(lines)
    env_file.write_text(new_content)
    
    print(f"Updated LANGS in .env file to include: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_env(['es', 'cn'])