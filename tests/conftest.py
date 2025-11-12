import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        yield client

@pytest.fixture
def authenticated_client(client):
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'testuser'
        sess['selected_appointment_id'] = 1
    return client

@pytest.fixture
def mock_db():
    def _mock_db(fetchone=None, fetchall=None, lastrowid=None, rowcount=1, side_effect=None):
        with patch('database.get_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.commit.return_value = None
            
            if side_effect is not None:
                mock_cursor.fetchone.side_effect = side_effect
            else:
                mock_cursor.fetchone.return_value = fetchone
                
            mock_cursor.fetchall.return_value = fetchall or []
            mock_cursor.lastrowid = lastrowid or 1
            mock_cursor.rowcount = rowcount
            
            return mock_cursor
    return _mock_db

# Add this fixture for auth routes
@pytest.fixture
def mock_auth_db():
    def _mock_db(fetchone=None, fetchall=None, lastrowid=None):
        with patch('auth.get_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            mock_cursor.fetchone.return_value = fetchone
            mock_cursor.fetchall.return_value = fetchall or []
            mock_cursor.lastrowid = lastrowid or 1
            
            return mock_cursor
    return _mock_db