import pytest
from database import verify_password, serialize_datetime, safe_close
from datetime import datetime, timedelta

class TestDatabase:
    def test_verify_password_none_hash(self):
        """Test password verification with None hash"""
        result = verify_password('password', None)
        assert result == False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash"""
        result = verify_password('password', 'invalid_hash')
        assert result == False

    def test_serialize_datetime(self):
        """Test datetime serialization"""
        test_date = datetime(2023, 12, 25, 10, 30, 45)
        result = serialize_datetime(test_date)
        assert result == '2023-12-25T10:30:45'

    def test_serialize_timedelta(self):
        """Test timedelta serialization"""
        delta = timedelta(hours=2, minutes=30)
        result = serialize_datetime(delta)  # This should handle timedelta
        assert isinstance(result, str)

    def test_serialize_other_types(self):
        """Test serialization with non-serializable types"""
        with pytest.raises(TypeError):
            serialize_datetime({"not": "serializable"})

    def test_safe_close_no_exception(self):
        """Test safe_close with valid connection"""
        # Mock connection
        class MockConnection:
            def __init__(self):
                self.connected = True
            
            def is_connected(self):
                return self.connected
            
            def close(self):
                self.connected = False

        conn = MockConnection()
        # This should not raise an exception
        safe_close(conn)
        assert conn.connected == False

    # Add this function to your database.py file
    def serialize(obj):
     """Serialize objects for JSON response - handles datetime and timedelta"""
     if isinstance(obj, datetime):
        return obj.isoformat()
     elif isinstance(obj, timedelta):
        return str(obj)
     raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def test_safe_close_with_exception(self):
        """Test safe_close when close raises exception"""
        class FaultyConnection:
            def is_connected(self):
                return True
            
            def close(self):
                raise Exception("Close error")
    
        conn = FaultyConnection()
        # This should not raise an exception despite the error
        safe_close(conn)  # Should complete without raising