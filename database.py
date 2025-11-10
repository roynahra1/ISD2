import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from typing import Any
from werkzeug.security import check_password_hash

# ----------------------------
# Database Configuration
# ----------------------------
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "isd"),
    "auth_plugin": "mysql_native_password"
}

def get_connection():
    return mysql.connector.connect(**db_config)

def serialize(val: Any) -> Any:
    """Convert datetime or timedelta to string for JSON responses"""
    if isinstance(val, (datetime, timedelta)):
        return str(val)
    return val

def _safe_close(cursor=None, conn=None):
    """Safely close MySQL cursor and connection."""
    for obj in (cursor, conn):
        try:
            if obj:
                obj.close()
        except Exception:
            pass

def verify_password(stored_hash: str | None, supplied: str) -> bool:
    """Verify a password safely using Werkzeug."""
    if not stored_hash:
        return False
    try:
        return check_password_hash(stored_hash, supplied)
    except Exception:
        return False