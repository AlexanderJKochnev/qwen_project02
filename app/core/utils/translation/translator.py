"""Translation service for database models."""

import asyncio
from typing import Dict, List, Type, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import class_mapper
from app.core.models.base_model import Base

# Try to import pymorphy2, but handle the case where it's not available
try:
    import pymorphy2  # for Russian noun cases
    HAS_PYMORPHY2 = True
except ImportError:
    pymorphy2 = None
    HAS_PYMORPHY2 = False


class TranslationService:
    """Service to handle translations for models with multilingual fields."""
    
    def __init__(self):
        """Initialize the translation service."""
        # Initialize morph analyzer for Russian if available
        if HAS_PYMORPHY2:
            self.morph = pymorphy2.MorphAnalyzer()
        else:
            self.morph = None
        
        # Language codes mapping
        self.language_codes = {
            'ru': 'name_ru',
            'fr': 'name_fr',
            # Add more languages as needed
        }
        
        # Translation dictionaries for different model types
        self.translation_dictionaries = {
            'country': {},
            'region': {},
            'subregion': {},
            'category': {},
            'subcategory': {},
            'food': {},
            'varietal': {},
        }
        
        # Load translation dictionaries
        self._load_translation_dictionaries()

    def _load_translation_dictionaries(self):
        """Load translation dictionaries for different model types."""
        # Countries translations
        self.translation_dictionaries['country'] = {
            'France': {'ru': 'Франция', 'fr': 'France'},
            'Italy': {'ru': 'Италия', 'fr': 'Italie'},
            'Spain': {'ru': 'Испания', 'fr': 'Espagne'},
            'Germany': {'ru': 'Германия', 'fr': 'Allemagne'},
            'United States': {'ru': 'Соединенные Штаты', 'fr': 'États-Unis'},
            'Australia': {'ru': 'Австралия', 'fr': 'Australie'},
            'Argentina': {'ru': 'Аргентина', 'fr': 'Argentine'},
            'Chile': {'ru': 'Чили', 'fr': 'Chili'},
            'South Africa': {'ru': 'Южная Африка', 'fr': 'Afrique du Sud'},
            'New Zealand': {'ru': 'Новая Зеландия', 'fr': 'Nouvelle-Zélande'},
        }
        
        # Regions translations (example - would be expanded in real implementation)
        self.translation_dictionaries['region'] = {
            'Bordeaux': {'ru': 'Бордо', 'fr': 'Bordeaux'},
            'Tuscany': {'ru': 'Тоскана', 'fr': 'Toscane'},
            'Rioja': {'ru': 'Рибера дель Дуэро', 'fr': 'Rioja'},
        }
        
        # Subregions translations
        self.translation_dictionaries['subregion'] = {
            'Margaux': {'ru': 'Марго', 'fr': 'Margaux'},
            'Chianti Classico': {'ru': 'Кьянти Классико', 'fr': 'Chianti Classico'},
        }
        
        # Categories translations
        self.translation_dictionaries['category'] = {
            'Wine': {'ru': 'Вино', 'fr': 'Vin'},
            'Spirits': {'ru': 'Спиртные напитки', 'fr': 'Spiritueux'},
            'Beer': {'ru': 'Пиво', 'fr': 'Bière'},
            'Cider': {'ru': 'Сидр', 'fr': 'Cidre'},
        }
        
        # Subcategories translations
        self.translation_dictionaries['subcategory'] = {
            'Red Wine': {'ru': 'Красное вино', 'fr': 'Vin rouge'},
            'White Wine': {'ru': 'Белое вино', 'fr': 'Vin blanc'},
            'Rose Wine': {'ru': 'Розовое вино', 'fr': 'Vin rosé'},
            'Vodka': {'ru': 'Водка', 'fr': 'Vodka'},
            'Whiskey': {'ru': 'Виски', 'fr': 'Whiskey'},
            'Gin': {'ru': 'Джин', 'fr': 'Gin'},
        }
        
        # Foods translations
        self.translation_dictionaries['food'] = {
            'Cheese': {'ru': 'Сыр', 'fr': 'Fromage'},
            'Chocolate': {'ru': 'Шоколад', 'fr': 'Chocolat'},
            'Meat': {'ru': 'Мясо', 'fr': 'Viande'},
            'Fish': {'ru': 'Рыба', 'fr': 'Poisson'},
            'Seafood': {'ru': 'Морепродукты', 'fr': 'Fruits de mer'},
            'Pasta': {'ru': 'Паста', 'fr': 'Pâtes'},
            'Pizza': {'ru': 'Пицца', 'fr': 'Pizza'},
        }
        
        # Varietals translations
        self.translation_dictionaries['varietal'] = {
            'Cabernet Sauvignon': {'ru': 'Каберне Совиньон', 'fr': 'Cabernet Sauvignon'},
            'Pinot Noir': {'ru': 'Пино Нуар', 'fr': 'Pinot noir'},
            'Chardonnay': {'ru': 'Шардоне', 'fr': 'Chardonnay'},
            'Sauvignon Blanc': {'ru': 'Совиньон Блан', 'fr': 'Sauvignon Blanc'},
            'Merlot': {'ru': 'Мерло', 'fr': 'Merlot'},
        }

    async def translate_model_records(
        self, 
        db_session: AsyncSession, 
        model_class: Type[Base],
        force_update: bool = False
    ) -> int:
        """
        Translate records for a given model.
        
        Args:
            db_session: Database session
            model_class: Model class to translate
            force_update: Whether to force update existing translations
            
        Returns:
            Number of records updated
        """
        # Get all records for the model
        stmt = select(model_class)
        result = await db_session.execute(stmt)
        records = result.scalars().all()
        
        updated_count = 0
        
        for record in records:
            updated = await self.translate_single_record(db_session, record, force_update)
            if updated:
                updated_count += 1
        
        if updated_count > 0:
            await db_session.commit()
        
        return updated_count

    async def translate_single_record(
        self, 
        db_session: AsyncSession, 
        record: Base, 
        force_update: bool = False
    ) -> bool:
        """
        Translate a single record.
        
        Args:
            db_session: Database session
            record: Record to translate
            force_update: Whether to force update existing translations
            
        Returns:
            True if record was updated, False otherwise
        """
        # Determine the model type
        model_type = record.__class__.__name__.lower()
        if model_type.endswith('model'):
            model_type = model_type[:-5]
        
        # Special handling for Food model (Russian noun cases)
        if model_type == 'food':
            return await self._translate_food_record(db_session, record, force_update)
        
        # Standard translation for other models
        return await self._translate_standard_record(db_session, record, model_type, force_update)

    async def _translate_food_record(
        self, 
        db_session: AsyncSession, 
        record: Base, 
        force_update: bool = False
    ) -> bool:
        """
        Translate a food record, handling Russian noun cases.
        
        Args:
            db_session: Database session
            record: Food record to translate
            force_update: Whether to force update existing translations
            
        Returns:
            True if record was updated, False otherwise
        """
        updated = False
        
        # Check if English name exists
        if not hasattr(record, 'name') or not record.name:
            return False
        
        english_name = record.name.strip()
        if not english_name:
            return False
        
        # Translate to French if needed
        if force_update or not getattr(record, 'name_fr', None):
            french_translation = await self._get_french_translation('food', english_name)
            if french_translation:
                setattr(record, 'name_fr', french_translation)
                updated = True
        
        # Translate to Russian if needed
        if force_update or not getattr(record, 'name_ru', None):
            russian_translation = await self._get_russian_translation('food', english_name)
            if russian_translation:
                setattr(record, 'name_ru', russian_translation)
                updated = True
        else:
            # Special case: if Russian translation exists, normalize it to nominative case
            current_ru = getattr(record, 'name_ru', None)
            if current_ru:
                normalized_ru = self._normalize_russian_noun_case(current_ru)
                if normalized_ru != current_ru:
                    setattr(record, 'name_ru', normalized_ru)
                    updated = True
        
        return updated

    async def _translate_standard_record(
        self, 
        db_session: AsyncSession, 
        record: Base, 
        model_type: str, 
        force_update: bool = False
    ) -> bool:
        """
        Translate a standard record (not Food).
        
        Args:
            db_session: Database session
            record: Record to translate
            model_type: Type of model
            force_update: Whether to force update existing translations
            
        Returns:
            True if record was updated, False otherwise
        """
        updated = False
        
        # Check if English name exists
        if not hasattr(record, 'name') or not record.name:
            return False
        
        english_name = record.name.strip()
        if not english_name:
            return False
        
        # Translate to French if needed
        if force_update or not getattr(record, 'name_fr', None):
            french_translation = await self._get_french_translation(model_type, english_name)
            if french_translation:
                setattr(record, 'name_fr', french_translation)
                updated = True
        
        # Translate to Russian if needed
        if force_update or not getattr(record, 'name_ru', None):
            russian_translation = await self._get_russian_translation(model_type, english_name)
            if russian_translation:
                setattr(record, 'name_ru', russian_translation)
                updated = True
        
        return updated

    async def _get_french_translation(self, model_type: str, english_name: str) -> Optional[str]:
        """Get French translation for a term."""
        if model_type in self.translation_dictionaries:
            translations = self.translation_dictionaries[model_type]
            if english_name in translations:
                return translations[english_name].get('fr')
        return None

    async def _get_russian_translation(self, model_type: str, english_name: str) -> Optional[str]:
        """Get Russian translation for a term."""
        if model_type in self.translation_dictionaries:
            translations = self.translation_dictionaries[model_type]
            if english_name in translations:
                return translations[english_name].get('ru')
        return None

    def _normalize_russian_noun_case(self, russian_text: str) -> str:
        """
        Normalize Russian noun to nominative case singular form.
        
        Args:
            russian_text: Russian text to normalize
            
        Returns:
            Normalized text in nominative case singular
        """
        # If pymorphy2 is not available, return the text as is
        if not self.morph:
            return russian_text
            
        try:
            words = russian_text.split()
            normalized_words = []
            
            for word in words:
                # Parse the word
                parsed = self.morph.parse(word)
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

    async def translate_all_models(
        self, 
        db_session: AsyncSession, 
        force_update: bool = False
    ) -> Dict[str, int]:
        """
        Translate records for all supported models.
        
        Args:
            db_session: Database session
            force_update: Whether to force update existing translations
            
        Returns:
            Dictionary with model names and number of updated records
        """
        from app.support.country.model import Country
        from app.support.region.model import Region
        from app.support.subregion.model import Subregion
        from app.support.category.model import Category
        from app.support.subcategory.model import Subcategory
        from app.support.food.model import Food
        from app.support.varietal.model import Varietal
        
        models_to_translate = [
            ('country', Country),
            ('region', Region),
            ('subregion', Subregion),
            ('category', Category),
            ('subcategory', Subcategory),
            ('food', Food),
            ('varietal', Varietal),
        ]
        
        results = {}
        
        for model_name, model_class in models_to_translate:
            try:
                count = await self.translate_model_records(db_session, model_class, force_update)
                results[model_name] = count
            except Exception as e:
                print(f"Error translating {model_name}: {e}")
                results[model_name] = 0
        
        return results


# Global instance of the translation service
translation_service = TranslationService()