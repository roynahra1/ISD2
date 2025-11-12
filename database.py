import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from typing import Any
from werkzeug.security import check_password_hash
from typing import Union, Optional, Any
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

import sqlite3
import os

def get_connection():
    """Get database connection with error handling"""
    try:
        # Make sure the path is correct
        db_path = os.path.join(os.path.dirname(__file__), 'appointments.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

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

def verify_password(stored_hash: Optional[str], supplied: str) -> bool:
    """Verify a password safely using Werkzeug."""
    if not stored_hash:
        return False
    try:
        return check_password_hash(stored_hash, supplied)
    except Exception:
        return False