#!/usr/bin/env python3
"""
Script to analyze and mark localized data fields in the codebase.
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

def find_localized_fields_in_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Find all localized fields in a file and return their line numbers, language, and content.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    localized_fields = []
    
    for line_num, line in enumerate(lines, 1):
        # Skip comment lines
        if line.strip().startswith('#'):
            continue
            
        # Find lines with localized field patterns (like name_ru, description_fr, etc.)
        # This regex looks for field names that end with _ru or _fr
        matches_ru = re.findall(r'\b\w+_ru\b', line)
        matches_fr = re.findall(r'\b\w+_fr\b', line)
        
        # Handle each language separately
        for match in matches_ru:
            # Add the full line for this language
            localized_fields.append((line_num, 'ru', line.strip()))
        
        for match in matches_fr:
            # Add the full line for this language
            localized_fields.append((line_num, 'fr', line.strip()))
    
    return localized_fields

def create_language_yaml_entry(file_path: Path, localized_fields: List[Tuple[int, str, str]]) -> Dict:
    """
    Create a YAML entry for the language.yaml file.
    """
    file_entries = {}
    
    # Group fields by language and create entries
    lang_counters = {'ru': 1, 'fr': 1}
    
    # Track which line has already been processed to avoid duplicates
    processed_lines = set()
    
    for line_num, lang, content in localized_fields:
        if (line_num, content) in processed_lines:
            continue  # Skip if already processed
            
        # Get field ID for this language
        field_id = f"{lang_counters[lang]:04d}"
        lang_counters[lang] += 1
        
        # Replace language suffixes with <xx> placeholder
        processed_content = re.sub(r'_ru\b', '_<xx>', content)
        processed_content = re.sub(r'_fr\b', '_<xx>', processed_content)
        
        file_entries[field_id] = processed_content
        processed_lines.add((line_num, content))
    
    return {str(file_path): file_entries}

def process_file(file_path: Path) -> Tuple[Dict, str]:
    """
    Process a single file: mark localized fields and return YAML entry.
    """
    print(f"Processing {file_path}...")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find localized fields
    localized_fields = find_localized_fields_in_file(file_path)
    
    if not localized_fields:
        return {}, content  # No changes needed
    
    # Create a mapping of language to field IDs
    lang_counters = {'ru': 1, 'fr': 1}
    
    # Track which lines have been processed to avoid duplicates
    processed_lines = set()
    
    # Process each localized field to add markers
    modified_lines = lines[:]
    
    # Process fields in reverse order to maintain correct line numbers after insertions
    for line_num, lang, content in sorted(localized_fields, key=lambda x: x[0], reverse=True):
        if (line_num, content) in processed_lines:
            continue  # Skip if already processed
            
        # Get field ID for this language
        field_id = f"{lang_counters[lang]:04d}"
        lang_counters[lang] += 1
        
        # Create markers
        start_marker = f"# {file_path} {lang} start {field_id}"
        end_marker = f"# {file_path} {lang} end {field_id}"
        
        # Add markers around the line
        line_idx = line_num - 1
        modified_lines.insert(line_idx, start_marker)
        modified_lines.insert(line_idx + 2, end_marker)  # +2 because we added start marker
        
        # Mark this line as processed
        processed_lines.add((line_num, content))
    
    # Create YAML entry
    yaml_entry = create_language_yaml_entry(file_path, localized_fields)
    
    # Join modified lines back
    modified_content = '\n'.join(modified_lines)
    
    return yaml_entry, modified_content

def main():
    # Find all Python files that might contain localized fields
    workspace_path = Path('/workspace')
    
    all_files = set()
    
    # Check each Python file for localized patterns
    for py_file in workspace_path.rglob('*.py'):
        # Skip test files and the script file itself
        if 'tests/' in str(py_file) or py_file.name == 'process_localized_fields.py':
            continue
            
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '_ru' in content or '_fr' in content:
                all_files.add(py_file)
    
    all_files = sorted(list(all_files))
    
    print(f"Found {len(all_files)} files with localized fields")
    
    # Process each file and collect YAML entries
    yaml_data = {}
    
    for file_path in all_files:
        yaml_entry, modified_content = process_file(file_path)
        
        # Update the file with marked content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        # Merge YAML entries
        for file_key, entries in yaml_entry.items():
            if file_key not in yaml_data:
                yaml_data[file_key] = {}
            yaml_data[file_key].update(entries)
    
    # Write language.yaml file
    with open('/workspace/language.yaml', 'w', encoding='utf-8') as f:
        f.write("file:\n")
        for file_path, entries in yaml_data.items():
            f.write(f"  {file_path}:\n")
            for field_id, content in entries.items():
                f.write(f"    {field_id}: {content}\n")
    
    print("Processing complete. language.yaml created and files updated.")

if __name__ == "__main__":
    main()