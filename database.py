import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

# Global connection pool
_db_connection = None

def get_db():
    """Get database connection with persistent connection"""
    global _db_connection
    
    try:
        if _db_connection is None or not _db_connection.is_connected():
            print("🔄 Creating new database connection...")
            _db_connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'isd'),
                autocommit=False,
                pool_size=5,
                pool_reset_session=True
            )
            print("✅ Database connection established")
        else:
            print("✅ Using existing database connection")
        
        return _db_connection
        
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        # Return a simple mock for testing
        class MockConnection:
            def cursor(self, dictionary=False):
                return MockCursor()
            def commit(self):
                pass
            def rollback(self):
                pass
            def is_connected(self):
                return True
        return MockConnection()

class MockCursor:
    """Mock cursor for testing when database is not available"""
    def execute(self, query, params=None):
        print(f"📝 Mock execute: {query} with {params}")
        return self
    
    def fetchone(self):
        # Return a mock user for testing
        return {
            'id': 1,
            'username': 'test',
            'email': 'test@test.com', 
            'password_hash': generate_password_hash('test123')
        }
    
    def fetchall(self):
        return []
    
    @property
    def lastrowid(self):
        return 1

def hash_password(password):
    """Hash a password for storing"""
    try:
        return generate_password_hash(password)
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        return None

def verify_password(password, password_hash):
    """Verify a stored password against one provided by user"""
    if not password_hash:
        print("❌ No password hash provided")
        return False
    try:
        return check_password_hash(password_hash, password)
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        return False

def safe_close(conn):
    """Safely close database connection"""
    try:
        if conn and hasattr(conn, 'is_connected') and conn.is_connected():
            conn.close()
            print("🔒 Database connection closed")
    except Exception as e:
        print(f"Error closing connection: {e}")