# app.support.migration.model
from app.core.config.project_config import settings
from app.core.models.base_model import Base, plural
# from app.service_registry import registers_search_update


class Migration(Base):
    """
    заглушка что бы core не ругались
    """
    lazy = settings.LAZY
    single_name = 'migration'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
