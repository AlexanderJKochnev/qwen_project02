# app/core/utils/translation_utils.py
import asyncio  # noqa: F401
import httpx
from typing import Dict, Optional, Any, List
from app.core.config.project_config import settings
import time


class TranslationService:
    """Base class for translation services"""
    
    def __init__(self, name: str, base_url: str, email: str = None):
        self.name = name
        self.base_url = base_url
        self.email = email
        self.last_request_time = 0
        self.rate_limit_remaining = float('inf')
        self.rate_limit_reset = 0
        
    async def translate(self, text: str, source_lang: str, target_lang: str, mark: str, test: bool = False) -> Optional[str]:
        raise NotImplementedError
    
    def update_rate_limits(self, response_headers):
        """Update rate limit information from response headers"""
        # Try to extract rate limit info from various possible header names
        rate_limit_headers = [
            'ratelimit-remaining-tokens',
            'x-ratelimit-remaining',
            'x-rate-limit-remaining',
            'retry-after',
            'ratelimit-reset',
            'x-ratelimit-reset'
        ]
        
        for header_name in rate_limit_headers:
            if header_name.lower() in response_headers:
                if 'remaining' in header_name.lower():
                    try:
                        self.rate_limit_remaining = int(response_headers[header_name.lower()])
                    except ValueError:
                        pass
                elif 'reset' in header_name.lower() or 'after' in header_name.lower():
                    try:
                        reset_value = response_headers[header_name.lower()]
                        if 'retry-after' in header_name.lower():
                            # retry-after might be in seconds
                            self.rate_limit_reset = time.time() + int(reset_value)
                        else:
                            self.rate_limit_reset = int(reset_value)
                    except ValueError:
                        pass


class MyMemoryTranslationService(TranslationService):
    """MyMemory translation service implementation"""
    
    def __init__(self):
        super().__init__(
            name="mymemory",
            base_url=settings.MYMEMORY_API_BASE_URL,
            email=settings.MYMEMORY_API_EMAIL
        )
    
    async def translate(self, text: str, source_lang: str, target_lang: str, mark: str, test: bool = False) -> Optional[str]:
        """Translate text using MyMemory translation service"""
        if not text or not text.strip():
            return text

        try:
            params = {
                "q": text,
                "langpair": f"{source_lang}|{target_lang}",
                "de": self.email
            }
            if test:
                print(f"MyMemoryTranslationService.translate.{params=}")
                return f"{text} <{mark}>"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                
                # Update rate limits from response headers
                self.update_rate_limits(dict(response.headers))
                
                response.raise_for_status()

                data = response.json()

                if data.get("responseStatus") == 200 and data.get("responseData"):
                    translated_text = data["responseData"]["translatedText"]
                    return f"{translated_text} <{mark}>"

                return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Too Many Requests
                self.rate_limit_remaining = 0
                print(f"MyMemory rate limit exceeded: {e}")
                return None
            print(f"MyMemory translation HTTP error: {e}")
            return None
        except Exception as e:
            print(f"MyMemory translation error: {e}")
            return None


class GrokCloudTranslationService(TranslationService):
    """GrokCloud translation service implementation"""
    
    def __init__(self):
        super().__init__(
            name="grokcloud",
            base_url=getattr(settings, 'GROKCLOUD_API_BASE_URL', 'https://api.grok.com/translate'),
            email=getattr(settings, 'GROKCLOUD_API_EMAIL', None)
        )
        self.api_key = getattr(settings, 'GROKCLOUD_API_KEY', '')
    
    async def translate(self, text: str, source_lang: str, target_lang: str, mark: str, test: bool = False) -> Optional[str]:
        """Translate text using GrokCloud translation service"""
        if not text or not text.strip():
            return text
            
        if not self.api_key:
            print("GrokCloud API key not configured")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
            
            if test:
                print(f"GrokCloudTranslationService.translate.{payload=}")
                return f"{text} <{mark}>"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, 
                    json=payload, 
                    headers=headers
                )
                
                # Update rate limits from response headers
                self.update_rate_limits(dict(response.headers))
                
                response.raise_for_status()
                
                data = response.json()
                
                if "translated_text" in data:
                    translated_text = data["translated_text"]
                    return f"{translated_text} <{mark}>"
                
                return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Too Many Requests
                self.rate_limit_remaining = 0
                print(f"GrokCloud rate limit exceeded: {e}")
                return None
            print(f"GrokCloud translation HTTP error: {e}")
            return None
        except Exception as e:
            print(f"GrokCloud translation error: {e}")
            return None


class TranslationManager:
    """Manages multiple translation services and selects the best one based on availability and rate limits"""
    
    def __init__(self):
        self.services = {}
        self.load_services()
    
    def load_services(self):
        """Load translation services based on configuration"""
        # Load MyMemory service
        if hasattr(settings, 'MYMEMORY_API_BASE_URL') and settings.MYMEMORY_API_BASE_URL:
            self.services['mymemory'] = MyMemoryTranslationService()
        
        # Load GrokCloud service if configured
        if hasattr(settings, 'GROKCLOUD_API_BASE_URL') and settings.GROKCLOUD_API_BASE_URL:
            self.services['grokcloud'] = GrokCloudTranslationService()
    
    async def translate_text(self, text: str, source_lang: str = "en",
                           target_lang: str = "ru",
                           mark: str = "ai",
                           test: bool = False) -> Optional[str]:
        """
        Main translation function that selects the best available service
        based on rate limits and availability
        """
        if not text or not text.strip():
            return text
        
        # Get all available services
        available_services = []
        
        for name, service in self.services.items():
            # Check if service has remaining quota or if we don't know the limit (assume infinite)
            if service.rate_limit_remaining > 0 or service.rate_limit_remaining == float('inf'):
                # Check if rate limit reset time has passed
                if time.time() >= service.rate_limit_reset:
                    available_services.append((name, service))
        
        # If no services have quota, wait for the earliest reset time
        if not available_services:
            min_reset_time = float('inf')
            for service in self.services.values():
                if service.rate_limit_reset < min_reset_time:
                    min_reset_time = service.rate_limit_reset
            
            if min_reset_time != float('inf') and time.time() < min_reset_time:
                # Wait until rate limit resets
                wait_time = min_reset_time - time.time()
                if wait_time > 0:
                    print(f"Waiting {wait_time:.2f}s for rate limit reset...")
                    await asyncio.sleep(wait_time)
        
        # Retry with potentially reset quotas
        available_services = []
        for name, service in self.services.items():
            if service.rate_limit_remaining > 0 or service.rate_limit_remaining == float('inf'):
                if time.time() >= service.rate_limit_reset:
                    available_services.append((name, service))
        
        # If still no services available, try all of them hoping they handle rate limiting gracefully
        if not available_services:
            available_services = list(self.services.items())
        
        # Try each available service in order
        for service_name, service in available_services:
            try:
                result = await service.translate(text, source_lang, target_lang, mark, test)
                if result is not None:
                    return result
            except Exception as e:
                print(f"Service {service_name} failed: {e}")
                continue
        
        return None  # All services failed


# Global translation manager instance
translation_manager = TranslationManager()


async def translate_text(text: str, source_lang: str = "en",
                         target_lang: str = "ru",
                         mark: str = "ai",
                         test: bool = False) -> Optional[str]:
    """
    Translate text using the best available translation service based on rate limits

    Args:
        text: Text to translate
        source_lang: Source language code (default: "en")
        target_lang: Target language code (default: "ru")
        mark:  отметка о машинном переводе
        test: used for test purpose only
    Returns:
        Translated text or None if translation failed
    """
    return await translation_manager.translate_text(text, source_lang, target_lang, mark, test)


def get_group_localized_fields(langs: list, default_lang: str, localized_fields: list) -> Dict[str, List[str]]:
    """Get dict of localized field names that should be translated"""
    languages = [f'_{lang}' if lang != default_lang else '' for lang in langs]
    result: dict = {}
    for field in localized_fields:
        result[field] = [f'{field}{lang}' for lang in languages]
    return result


def get_field_language(field_name: str) -> Optional[str]:
    """Extract language code from field name"""
    if len(field_name) < 3 or field_name[-3] != '_':
        return settings.DEFAULT_LANG
    lang_code = field_name[-2:]
    # Check if the extracted code is in the configured languages
    if lang_code in settings.LANGUAGES:
        return lang_code
    return settings.DEFAULT_LANG


async def fill_missing_translations(data: Dict[str, Any], test: bool = False) -> Dict[str, Any]:
    """
    Fill missing translations in data dictionary using available translations

    Args:
        data: Dictionary containing fields that may need translation

    Returns:
        Updated dictionary with filled translations
    """
    if not data:
        return data

    updated_data = data.copy()

    # language
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    localized_fields = settings.FIELDS_LOCALIZED
    mark = settings.MACHINE_TRANSLATION_MARK
    # Group fields by their base name {'name': ['name', 'name_ru', 'name_fr', ...], ...}
    field_groups = get_group_localized_fields(langs, default_lang, localized_fields)

    # Process each group of related fields
    for base_name, fields in field_groups.items():
        # Check which fields are filled
        # {'name': 'text', 'name_ru': 'текст', ...}
        filled_fields = {field: data.get(field) for field in fields if data.get(field)}

        # Skip if no source for translation
        if not filled_fields:
            continue

        # Determine source field priority: prefer First in language, then Second, then Next
        source_field = None
        source_value = None

        # Find source -- first non empty fields
        for lang in langs:
            for field_name, value in filled_fields.items():
                if get_field_language(field_name) == lang and value:
                    source_field = field_name
                    source_value = value
                    source_lang = lang
                    break
            if source_field:
                break

        if not source_value:    # no source found
            continue            # skip translation

        # Fill missing translations
        for field in fields:
            if field not in filled_fields:  # Field is missing
                target_lang = get_field_language(field)
                if target_lang and target_lang != source_lang:
                    # Translate from source to target
                    translated_text = await translate_text(
                        source_value,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        mark=mark
                    )

                    if translated_text:
                        updated_data[field] = translated_text

    return updated_data
