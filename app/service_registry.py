# app/service_registry.py
"""
    здесь явно регистрируются все
    сервисы
    репозитории
    схемы
    и даны методы их регистрации и получения списком и по имени файла / типу схемы

"""

_SERVICE_REGISTRY: dict = {}
_REPOSITORY_REGISTRY: dict = {}
_PYSCHEMA_REGISTRY: dict = {}


def register_pyschema(name: str, cls):
    _PYSCHEMA_REGISTRY[name.lower()] = cls


def get_pyschema(name: str):
    return _PYSCHEMA_REGISTRY.get(name.lower())


def get_all_pyschema():
    return _PYSCHEMA_REGISTRY.copy()


def register_repo(name: str, cls):
    _REPOSITORY_REGISTRY[name.lower()] = cls


def get_repo(name: str):
    return _REPOSITORY_REGISTRY.get(name.lower())


def get_all_repo():
    return _REPOSITORY_REGISTRY.copy()


def register_service(name: str, cls):
    _SERVICE_REGISTRY[name.lower()] = cls
    # Register the global search service
    if name.lower() == 'search':
        _SERVICE_REGISTRY['search_service'] = cls


def get_service(name: str):
    # Lazy load search service if not already loaded
    """if name.lower() == 'search_service' and 'search_service' not in _SERVICE_REGISTRY:
        # Import here to avoid circular imports
        from app.core.services.search_service import search_service
        _SERVICE_REGISTRY['search_service'] = search_service"""
    return _SERVICE_REGISTRY.get(name.lower())


def get_all_services():
    return _SERVICE_REGISTRY.copy()
