import os
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv

load_dotenv()

# ── Connection Pool (max 5 concurrent DB connections) ──────────────────────
_pool = MySQLConnectionPool(
    pool_name="learnify_pool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),        # No fallback — fail loudly if missing
    database=os.getenv("DB_NAME", "learnifydb"),
)

def get_db():
    """Return a pooled connection. Caller must close it to return it to pool."""
    return _pool.get_connection()
