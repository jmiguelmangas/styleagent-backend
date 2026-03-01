from app.core.ai import AIStyleGenerator, get_ai_generator_instance
from app.storage.base import Store
from app.storage.store_factory import get_store_instance


def get_store() -> Store:
    return get_store_instance()


def get_ai_generator() -> AIStyleGenerator:
    return get_ai_generator_instance()
