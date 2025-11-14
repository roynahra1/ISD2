import pytest
import sys
import os
<<<<<<< HEAD
from unittest.mock import Mock, patch
from werkzeug.security import generate_password_hash

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def app():
    """Create test Flask app."""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Authenticated test client."""
    with client.session_transaction() as session:
        session['logged_in'] = True
        session['username'] = 'testuser'
        session['selected_appointment_id'] = 1
        session['selected_appointment'] = {
            'Appointment_id': 1,
            'Date': '2024-01-15',
            'Time': '10:00',
            'Car_plate': 'TEST123'
        }
    return client

@pytest.fixture
def mock_db_success():
    """Mock database connection for successful operations."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.start_transaction = Mock()
    mock_conn.commit = Mock()
    mock_conn.rollback = Mock()
    
    # Default successful responses
    mock_cursor.fetchone.return_value = None  # No conflicts by default
    mock_cursor.fetchall.return_value = []    # Empty by default
    mock_cursor.lastrowid = 1                 # Success ID
    
    with patch('routes.auth_routes.get_connection', return_value=mock_conn), \
         patch('routes.appointment_routes.get_connection', return_value=mock_conn):
        yield mock_conn, mock_cursor

@pytest.fixture
def mock_db_failure():
    """Mock database connection for failure scenarios."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.start_transaction = Mock()
    mock_conn.commit = Mock()
    mock_conn.rollback = Mock()
    
    # Default failure responses
    mock_cursor.fetchone.side_effect = Exception("Database error")
    mock_cursor.fetchall.side_effect = Exception("Database error")
    
    with patch('routes.auth_routes.get_connection', return_value=mock_conn), \
         patch('routes.appointment_routes.get_connection', return_value=mock_conn):
        yield mock_conn, mock_cursor

@pytest.fixture
def sample_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }

@pytest.fixture
def sample_appointment_data():
    return {
        "car_plate": "TEST123",
        "date": "2024-12-31",  # Future date
        "time": "10:00",
        "service_ids": [1, 2],
        "notes": "Test appointment"
    }
=======
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
>>>>>>> 8a7626db99416992d066a2ebfc1b43e7caff1293
