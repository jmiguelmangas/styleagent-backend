from app.storage.fs_store import FSStore
from app.storage.mongo_store import MongoStore
from app.storage.store_factory import get_store_instance


def test_store_factory_defaults_to_fs(monkeypatch) -> None:
    monkeypatch.delenv("STYLEAGENT_DB_URL", raising=False)
    get_store_instance.cache_clear()
    store = get_store_instance()
    assert isinstance(store, FSStore)


def test_store_factory_selects_mongo_for_mongodb_url(monkeypatch) -> None:
    monkeypatch.setenv("STYLEAGENT_DB_URL", "mongodb://mongodb:27017/styleagent")
    monkeypatch.setenv("MONGO_DB_NAME", "styleagent")
    get_store_instance.cache_clear()
    store = get_store_instance()
    assert isinstance(store, MongoStore)
    assert store.db_url == "mongodb://mongodb:27017/styleagent"
    assert store.db_name == "styleagent"

