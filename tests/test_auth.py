import pytest
import json
from unittest.mock import patch
from tests.conftest import client, mock_db
from werkzeug.security import generate_password_hash

class TestAuth:
    # Signup Tests
    def test_signup_success(self, client, mock_db):
        mock_db(fetchone=None, lastrowid=100)
        response = client.post('/signup', json={
            'username': 'uniqueuser123',
            'email': 'unique123@example.com', 
            'password': 'secure123'
        })
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['status'] == 'success'

    def test_signup_missing_fields(self, client):
        response = client.post('/signup', json={})
        data = json.loads(response.data)
        assert response.status_code == 400
        assert data['status'] == 'error'

    def test_signup_short_password(self, client):
        response = client.post('/signup', json={
            'username': 'u', 'email': 'e@x.com', 'password': '123'
        })
        data = json.loads(response.data)
        assert response.status_code == 400
        assert data['status'] == 'error'

    def test_signup_duplicate_username(self, client, mock_db):
        mock_cursor = mock_db(fetchone=(1,))
        response = client.post('/signup', json={
            'username': 'existing', 
            'email': 'test@example.com', 
            'password': 'secure123'
        })
        data = json.loads(response.data)
        assert response.status_code == 409
        assert data['status'] == 'error'

    def test_signup_duplicate_email(self, client, mock_db):
        mock_cursor = mock_db(side_effect=[None, (1,)])
        response = client.post('/signup', json={
            'username': 'newuser',
            'email': 'existing@example.com', 
            'password': 'secure123'
        })
        data = json.loads(response.data)
        assert response.status_code == 409
        assert data['status'] == 'error'

    def test_signup_db_error(self, client):
        with patch('auth.signup.get_connection', side_effect=Exception("DB error")):
            response = client.post('/signup', json={
                'username': 'u', 'email': 'e@x.com', 'password': 'secure'
            })
            data = json.loads(response.data)
            assert response.status_code == 500
            assert data['status'] == 'error'

    # Login Tests
    def test_login_success(self, client, mock_db):
        password = "password123"
        hashed_pw = generate_password_hash(password)
        mock_db(fetchone=(1, hashed_pw))  # Include user_id in response
        
        response = client.post('/login', json={
            'username': 'testuser',
            'password': password
        })
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['status'] == 'success'

    def test_login_invalid_user(self, client, mock_db):
        mock_db(fetchone=None)
        response = client.post('/login', json={
            'username': 'ghost', 
            'password': 'wrong'
        })
        data = json.loads(response.data)
        assert response.status_code == 401
        assert data['status'] == 'error'

    def test_login_missing_fields(self, client):
        response = client.post('/login', json={})
        data = json.loads(response.data)
        assert response.status_code == 400
        assert data['status'] == 'error'

    def test_login_wrong_password(self, client, mock_db):
        password = "rightpassword"
        wrong_password = "wrongpassword"
        hashed_pw = generate_password_hash(password)
        
        mock_db(fetchone=(1, hashed_pw))
        
        response = client.post('/login', json={
            'username': 'testuser',
            'password': wrong_password
        })
        data = json.loads(response.data)
        assert response.status_code == 401
        assert data['status'] == 'error'

    # Logout Tests
    def test_logout(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
        response = client.post('/logout')
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['status'] == 'success'

    def test_logout_without_login(self, client):
        response = client.post('/logout')
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['status'] == 'success'

    # Auth Status Tests
    def test_auth_status_logged_out(self, client):
        response = client.get('/auth/status')
        data = json.loads(response.data)
        assert data['logged_in'] == False
        assert data['status'] == 'success'

    def test_auth_status_logged_in(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'testuser'
        response = client.get('/auth/status')
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['logged_in'] == True
        assert data['username'] == 'testuser'

    def test_auth_status_contains_username(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'Roy'
        response = client.get('/auth/status')
        data = json.loads(response.data)
        assert data['logged_in'] == True
        assert data['username'] == 'Roy'

    # Edge Cases
    def test_signup_empty_username(self, client):
        response = client.post('/signup', json={
            'username': '   ',
            'email': 'test@example.com',
            'password': 'password123'
        })
        data = json.loads(response.data)
        assert response.status_code == 400
        assert data['status'] == 'error'

    def test_signup_empty_email(self, client):
        response = client.post('/signup', json={
            'username': 'testuser',
            'email': '   ',
            'password': 'password123'
        })
        data = json.loads(response.data)
        assert response.status_code == 400
        assert data['status'] == 'error'

    def test_login_empty_credentials(self, client):
        response = client.post('/login', json={
            'username': '   ',
            'password': '   '
        })
        data = json.loads(response.data)
        assert response.status_code == 400
        assert data['status'] == 'error'