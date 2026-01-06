#!/usr/bin/env python3
"""
Main script to run all dynamic generation scripts for handling localized fields based on LANGS configuration.
"""
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config.project_config import settings


def run_all_generations():
    """Run all dynamic generation scripts."""
    print(f"Starting dynamic generation for LANGS: {settings.LANGS}")
    print(f"Languages: {settings.LANGUAGES}")
    print(f"Default language: {settings.DEFAULT_LANG}")
    print(f"Localized fields: {settings.FIELDS_LOCALIZED}")
    
    # Import and run each generation script
    print("\n1. Generating dynamic models...")
    from scripts.generate_dynamic_models import update_drink_model, generate_pytest_for_dynamic_models
    update_drink_model()
    generate_pytest_for_dynamic_models()
    
    print("\n2. Generating dynamic schemas...")
    from scripts.generate_dynamic_schemas import generate_lang_schemas, generate_dynamic_schemas_for_models, generate_pytest_for_dynamic_schemas
    generate_lang_schemas()
    generate_dynamic_schemas_for_models()
    generate_pytest_for_dynamic_schemas()
    
    print("\n3. Generating dynamic services...")
    from scripts.generate_dynamic_services import update_item_service, update_translation_utils, generate_pytest_for_dynamic_services
    update_item_service()
    update_translation_utils()
    generate_pytest_for_dynamic_services()
    
    print("\n4. Generating dynamic frontend...")
    from scripts.generate_dynamic_frontend import update_handbook_create_form, generate_pytest_for_dynamic_frontend
    update_handbook_create_form()
    generate_pytest_for_dynamic_frontend()
    
    print("\n5. Running tests to verify changes...")
    # Run basic tests to ensure the changes work correctly
    try:
        # Test that the settings are loaded correctly
        langs = settings.LANGUAGES
        default_lang = settings.DEFAULT_LANG
        localized_fields = settings.FIELDS_LOCALIZED
        
        print(f"  ✓ LANGS: {langs}")
        print(f"  ✓ Default language: {default_lang}")
        print(f"  ✓ Localized fields: {localized_fields}")
        
        # Test that we can import the updated modules
        from app.support.drink.model import Lang
        from app.core.utils.translation_utils import get_field_language, get_base_field_name
        print("  ✓ Updated modules imported successfully")
        
        # Test translation utilities
        for lang in langs:
            if lang != default_lang:
                test_field = f"title_{lang}"
                detected = get_field_language(test_field)
                assert detected == lang, f"Expected {lang}, got {detected}"
        
        print("  ✓ Translation utilities working correctly")
        
    except Exception as e:
        print(f"  ✗ Error during verification: {e}")
        raise
    
    print("\n✓ All dynamic generation completed successfully!")
    print(f"  - Generated dynamic models for {len(langs)} languages")
    print(f"  - Updated schemas to handle {len(localized_fields)} localized fields")
    print(f"  - Updated services for dynamic language support")
    print(f"  - Updated frontend forms for {len(langs)} languages")


def clean_workspace():
    """Clean up temporary files and backups."""
    import os
    import glob
    
    # Remove backup files
    backup_pattern = str(Path(__file__).parent.parent / "**" / "*.py.backup")
    for backup_file in glob.glob(backup_pattern, recursive=True):
        try:
            os.remove(backup_file)
            print(f"Removed backup file: {backup_file}")
        except:
            pass
    
    print("Cleaned up backup files")


if __name__ == "__main__":
    try:
        run_all_generations()
        clean_workspace()
        print("\n🎉 Dynamic localization system generation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during dynamic generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)