#!/usr/bin/env python3
"""
Script to remove language codes from .env file
"""
from pathlib import Path

def remove_language_from_env(lang_codes: list):
    """Remove language codes from the LANGS variable in .env file"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print(f"Error: {env_file} does not exist")
        return False
    
    content = env_file.read_text()
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.startswith('LANGS='):
            current_langs = line.split('=')[1]  # Get current languages
            current_lang_list = [lang.strip() for lang in current_langs.split(',')]
            
            # Remove specified languages
            new_lang_list = [lang for lang in current_lang_list if lang not in lang_codes]
            
            new_langs = ','.join(new_lang_list)
            lines[i] = f'LANGS={new_langs}'
            break
    
    new_content = '\n'.join(lines)
    env_file.write_text(new_content)
    
    print(f"Removed languages from .env file: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_env(['es', 'cn'])