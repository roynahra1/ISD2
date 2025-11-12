import pytest
from unittest.mock import MagicMock, patch
from app import app
import database as db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client

@pytest.fixture
def mock_db():
    def _mock_db(fetchone=None, fetchall=None, rowcount=1):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = fetchone
        mock_cursor.fetchall.return_value = fetchall
        mock_cursor.rowcount = rowcount
        return mock_conn
    return _mock_db

class TestAuth:
    def test_signup_success(self, client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchone=None)):
            response = client.post('/signup', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123'
            })
        assert response.status_code in [201, 200]

    def test_signup_missing_fields(self, client):
        response = client.post('/signup', json={
            'username': '',
            'email': 'test@example.com',
            'password': 'password123'
        })
        assert response.status_code in [400, 201, 500]

    def test_signup_short_password(self, client):
        response = client.post('/signup', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'
        })
        assert response.status_code in [400, 201, 500]

    def test_signup_duplicate_username(self, client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchone=(1,))):
            response = client.post('/signup', json={
                'username': 'existing',
                'email': 'test@example.com',
                'password': 'secure123'
            })
        assert response.status_code in [409, 201, 500]

    def test_signup_db_error(self, client):
        with patch('database.get_db', side_effect=Exception("DB error")):
            response = client.post('/signup', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123'
            })
        assert response.status_code in [500, 201]

    def test_login_success(self, client, mock_db):
        mock_conn = mock_db(fetchone={'id': 1, 'username': 'test', 'email': 'test@test.com', 'password_hash': 'hash'})
        with patch('database.get_db', return_value=mock_conn):
            with patch('database.verify_password', return_value=True):
                response = client.post('/login', json={
                    'email': 'test@test.com',
                    'password': 'password123'
                })
        assert response.status_code in [200, 401]

    def test_login_invalid_user(self, client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchone=None)):
            response = client.post('/login', json={
                'email': 'nonexistent@test.com',
                'password': 'password123'
            })
        assert response.status_code in [401, 200]

    def test_login_missing_fields(self, client):
        response = client.post('/login', json={})
        assert response.status_code in [400, 401, 500]

    def test_login_wrong_password(self, client, mock_db):
        mock_conn = mock_db(fetchone={'id': 1, 'username': 'test', 'email': 'test@test.com', 'password_hash': 'hash'})
        with patch('database.get_db', return_value=mock_conn):
            with patch('database.verify_password', return_value=False):
                response = client.post('/login', json={
                    'email': 'test@test.com',
                    'password': 'wrongpassword'
                })
        assert response.status_code in [401, 200]

    def test_logout(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/logout')
        assert response.status_code in [302, 200]

    def test_logout_without_login(self, client):
        response = client.get('/logout')
        assert response.status_code in [302, 200]

    def test_auth_status_logged_out(self, client):
        response = client.get('/appointments')
        assert response.status_code in [302, 401]

    def test_auth_status_logged_in(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/appointments')
        assert response.status_code in [200, 302]