import os
from dotenv import load_dotenv
from deepagents.backends import StateBackend, StoreBackend, CompositeBackend

load_dotenv()
from utils.utils import GCSObjectBackend, InMemoryObjectBackend

GCS_ACCESS_KEY = os.getenv("GCS_ACCESS_KEY")
GCS_SECRET_KEY = os.getenv("GCS_SECRET_KEY")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
DB_URI = os.getenv("DB_URI")
USE_GCS_BACKEND = os.getenv("USE_GCS_BACKEND", "false").lower() in ("1", "true", "yes")
USE_SQL_STORE = os.getenv("USE_SQL_STORE", "false").lower() in ("1", "true", "yes")

def _init_store():
    if USE_SQL_STORE and DB_URI:
        from langgraph.store.postgres import PostgresStore

        store_ctx = PostgresStore.from_conn_string(DB_URI)
        store = store_ctx.__enter__()
        store.setup()
        print("Store setup complete.")
        return store

    try:
        from langgraph.store.memory import InMemoryStore
    except ImportError:
        try:
            from langgraph.store.memory import MemoryStore as InMemoryStore
        except ImportError:
            return None

    store_ctx = InMemoryStore()
    store = store_ctx.__enter__() if hasattr(store_ctx, "__enter__") else store_ctx
    if hasattr(store, "setup"):
        store.setup()
    return store

_STORE = _init_store()

def production_backend_factory(rt):
    """
    Factory to inject user-specific context into backends.
    'rt' is the ToolRuntime providing access to the config.
    """
    # FIX: Safely access config. 'rt' might not have 'config' in all contexts.
    # We try to get 'config' or fallback to an empty dict.
    # If rt has a 'context' attribute that holds config, we could try that too.
    config = getattr(rt, "config", {}) or {} 
    
    # Extract user_id from the configurable metadata passed during invocation
    user_info = config.get("configurable", {})
    user_id = user_info.get("user_id", "anonymous_user")

    use_gcs = USE_GCS_BACKEND and BUCKET_NAME and GCS_ACCESS_KEY and GCS_SECRET_KEY
    results_backend = (
        GCSObjectBackend(
            bucket_name=BUCKET_NAME,
            aws_access_key_id=GCS_ACCESS_KEY,
            aws_secret_access_key=GCS_SECRET_KEY,
            prefix=f"professor-research-agent/users/{user_id}/results/",
        )
        if use_gcs
        else InMemoryObjectBackend(prefix=f"professor-research-agent/users/{user_id}/results/")
    )

    return CompositeBackend(
        # Ephemeral scratchpad (isolated by thread_id automatically)
        default=StateBackend(rt),

        routes={
            # StoreBackend uses in-memory by default; enable SQL with USE_SQL_STORE=true.
            "/context/": StoreBackend(rt),
            "/memories/": StoreBackend(rt),
            # Store results in-memory by default; enable GCS with USE_GCS_BACKEND=true.
            "/results/": results_backend,
        }
    )
