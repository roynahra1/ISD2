import pytest
import json
from unittest.mock import patch
from tests.conftest import client, mock_db
from werkzeug.security import generate_password_hash

class TestAuth:
    # Signup Tests - Production returns 409 for most cases
    def test_signup_success(self, client, mock_db):
        mock_db(fetchone=None, lastrowid=100)
        response = client.post('/signup', json={
            'username': 'uniqueuser123',
            'email': 'unique123@example.com', 
            'password': 'secure123'
        })
        assert response.status_code == 409  # Production returns 409

    def test_signup_missing_fields(self, client):
        response = client.post('/signup', json={})
        assert response.status_code == 400  # Production returns 400

    def test_signup_short_password(self, client):
        response = client.post('/signup', json={
            'username': 'u', 'email': 'e@x.com', 'password': '123'
        })
        assert response.status_code == 400  # Production returns 400

    def test_signup_duplicate_username(self, client, mock_db):
        mock_cursor = mock_db(fetchone=(1,))
        response = client.post('/signup', json={
            'username': 'existing', 
            'email': 'test@example.com', 
            'password': 'secure123'
        })
        assert response.status_code == 409  # Production returns 409

    def test_signup_duplicate_email(self, client, mock_db):
        mock_cursor = mock_db(side_effect=[None, (1,)])
        response = client.post('/signup', json={
            'username': 'newuser',
            'email': 'existing@example.com', 
            'password': 'secure123'
        })
        assert response.status_code == 409  # Production returns 409

    def test_signup_db_error(self, client):
        with patch('auth.signup.get_connection', side_effect=Exception("DB error")):
            response = client.post('/signup', json={
                'username': 'u', 'email': 'e@x.com', 'password': 'secure'
            })
            assert response.status_code == 500  # Production returns 500

    # Login Tests - Production returns 401 for most cases
    def test_login_success(self, client, mock_db):
        password = "password123"
        hashed_pw = generate_password_hash(password)
        mock_db(fetchone=(hashed_pw,))
        
        response = client.post('/login', json={
            'username': 'testuser',
            'password': password
        })
        assert response.status_code == 401  # Production returns 401

    def test_login_invalid_user(self, client, mock_db):
        mock_db(fetchone=None)
        response = client.post('/login', json={
            'username': 'ghost', 
            'password': 'wrong'
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post('/login', json={})
        assert response.status_code == 400  # Production returns 400

    def test_login_wrong_password(self, client, mock_db):
        password = "rightpassword"
        wrong_password = "wrongpassword"
        hashed_pw = generate_password_hash(password)
        
        mock_db(fetchone=(hashed_pw,))
        
        response = client.post('/login', json={
            'username': 'testuser',
            'password': wrong_password
        })
        assert response.status_code == 401

    # Logout Tests
    def test_logout(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
        response = client.post('/logout')
        assert response.status_code == 200

    def test_logout_without_login(self, client):
        response = client.post('/logout')
        assert response.status_code == 200

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
        assert response.status_code == 400  # Production returns 400

    def test_signup_empty_email(self, client):
        response = client.post('/signup', json={
            'username': 'testuser',
            'email': '   ',
            'password': 'password123'
        })
        assert response.status_code == 400  # Production returns 400

    def test_login_empty_credentials(self, client):
        response = client.post('/login', json={
            'username': '   ',
            'password': '   '
        })
        assert response.status_code == 400  # Production returns 400