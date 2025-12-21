"""Model mixin for automatic translation during save operations."""

from sqlalchemy.orm import Session

# Import translation service with error handling
try:
    from .translator import translation_service, HAS_PYMORPHY2
except Exception:
    # If translation service fails to initialize, create a mock object
    class MockTranslationService:
        def __init__(self):
            self.morph = None
            self.translation_dictionaries = {
                'country': {},
                'region': {},
                'subregion': {},
                'category': {},
                'subcategory': {},
                'food': {},
                'varietal': {},
            }
    
    translation_service = MockTranslationService()
    HAS_PYMORPHY2 = False


class TranslatableMixin:
    """Mixin to provide automatic translation functionality for models."""
    
    def translate_before_save(self, db_session: Session = None):
        """
        Translate the model fields before saving if they're empty.
        
        Args:
            db_session: Database session for async operations (if needed)
        """
        # Only translate if name field exists and is not empty
        if not hasattr(self, 'name') or not self.name:
            return
        
        # Skip if both translations already exist (unless we want to force update)
        if hasattr(self, 'name_ru') and hasattr(self, 'name_fr'):
            if self.name_ru and self.name_fr:
                # Both translations exist, don't override unless it's a food model
                if self.__class__.__name__.lower() != 'food':
                    return
        
        # Determine the model type for selecting the right translation dictionary
        model_type = self.__class__.__name__.lower()
        if model_type.endswith('model'):
            model_type = model_type[:-5]
        
        # Special handling for Food model
        if model_type == 'food':
            self._translate_food_entry()
        else:
            self._translate_standard_entry(model_type)
    
    def _translate_food_entry(self):
        """Translate food entry with special Russian case handling."""
        if not hasattr(self, 'name') or not self.name:
            return
        
        english_name = self.name.strip()
        
        # Translate to French if needed
        if not getattr(self, 'name_fr', None):
            french_translation = self._get_french_translation('food', english_name)
            if french_translation:
                setattr(self, 'name_fr', french_translation)
        
        # Translate to Russian if needed
        if not getattr(self, 'name_ru', None):
            russian_translation = self._get_russian_translation('food', english_name)
            if russian_translation:
                setattr(self, 'name_ru', russian_translation)
        else:
            # Special case: normalize existing Russian translation to nominative case
            current_ru = getattr(self, 'name_ru', None)
            if current_ru:
                normalized_ru = self._normalize_russian_noun_case(current_ru)
                if normalized_ru != current_ru:
                    setattr(self, 'name_ru', normalized_ru)
    
    def _translate_standard_entry(self, model_type: str):
        """Translate standard entry (not Food)."""
        if not hasattr(self, 'name') or not self.name:
            return
        
        english_name = self.name.strip()
        
        # Translate to French if needed
        if not getattr(self, 'name_fr', None):
            french_translation = self._get_french_translation(model_type, english_name)
            if french_translation:
                setattr(self, 'name_fr', french_translation)
        
        # Translate to Russian if needed
        if not getattr(self, 'name_ru', None):
            russian_translation = self._get_russian_translation(model_type, english_name)
            if russian_translation:
                setattr(self, 'name_ru', russian_translation)
    
    def _get_french_translation(self, model_type: str, english_name: str) -> str:
        """Get French translation for a term."""
        # For now, we'll use the global translation service
        # In a real implementation, this would be asynchronous
        try:
            # Access the translation dictionaries directly
            if model_type in translation_service.translation_dictionaries:
                translations = translation_service.translation_dictionaries[model_type]
                if english_name in translations:
                    return translations[english_name].get('fr')
        except Exception:
            pass
        return None
    
    def _get_russian_translation(self, model_type: str, english_name: str) -> str:
        """Get Russian translation for a term."""
        try:
            # Access the translation dictionaries directly
            if model_type in translation_service.translation_dictionaries:
                translations = translation_service.translation_dictionaries[model_type]
                if english_name in translations:
                    return translations[english_name].get('ru')
        except Exception:
            pass
        return None
    
    def _normalize_russian_noun_case(self, russian_text: str) -> str:
        """Normalize Russian noun to nominative case singular form."""
        # If pymorphy2 is not available, return the text as is
        if not HAS_PYMORPHY2 or not translation_service.morph:
            return russian_text
            
        try:
            # Using the global translation service's morph analyzer
            morph = translation_service.morph
            words = russian_text.split()
            normalized_words = []
            
            for word in words:
                # Parse the word
                parsed = morph.parse(word)
                if parsed:
                    # Get the normal form (nominative case, singular)
                    normal_form = parsed[0].normal_form
                    normalized_words.append(normal_form)
                else:
                    # If parsing fails, keep the original word
                    normalized_words.append(word)
            
            return ' '.join(normalized_words)
        except Exception:
            # If normalization fails, return original text
            return russian_text


# Alternative approach: A decorator or function that can be called during model operations
async def translate_model_instance(model_instance, db_session=None):
    """
    Translate a model instance before saving.
    
    Args:
        model_instance: Instance of a model to translate
        db_session: Database session for async operations
    """
    if hasattr(model_instance, 'translate_before_save'):
        model_instance.translate_before_save(db_session)
    else:
        # If the model doesn't have the mixin, we can still apply translation
        translator = translation_service
        await translator.translate_single_record(db_session, model_instance, force_update=False)