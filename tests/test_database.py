import pytest
from database import verify_password, serialize, _safe_close
from datetime import datetime, timedelta

class TestDatabase:
    def test_verify_password_none_hash(self):
        assert verify_password(None, 'any') == False

    def test_verify_password_invalid_hash(self):
        assert verify_password('not_a_hash', 'any') == False

    def test_serialize_datetime(self):
        dt = datetime(2025, 12, 1, 10, 30)
        result = serialize(dt)
        assert isinstance(result, str)

    def test_serialize_timedelta(self):
        td = timedelta(hours=2)
        result = serialize(td)
        assert isinstance(result, str)

    def test_serialize_other_types(self):
        assert serialize('string') == 'string'
        assert serialize(123) == 123
        assert serialize([1, 2, 3]) == [1, 2, 3]

    def test_safe_close_no_exception(self):
        _safe_close()

    def test_safe_close_with_exception(self):
        class FailingObject:
            def close(self):
                raise Exception("Close failed")
        
        _safe_close(FailingObject(), FailingObject())