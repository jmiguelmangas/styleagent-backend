from app.storage.base import Store
from app.storage.store_factory import get_store_instance


def get_store() -> Store:
    return get_store_instance()
