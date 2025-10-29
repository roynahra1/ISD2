import unittest
from unittest.mock import patch, MagicMock
from login import app, sha1_hash  # assuming your Flask app is named login.py

class LoginTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.valid_username = 'roy'
        self.valid_password = 'abc123'
        self.hashed_password = sha1_hash(self.valid_password)

    @patch('login.mysql.connector.connect')
    def test_successful_login(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [self.hashed_password]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        response = self.client.post('/login', json={
            'username': self.valid_username,
            'password': self.valid_password
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['message'], 'Login successful')

    @patch('login.mysql.connector.connect')
    def test_invalid_password(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ['wronghash']

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        response = self.client.post('/login', json={
            'username': self.valid_username,
            'password': self.valid_password
        })

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()['message'], 'Invalid username or password')

    def test_missing_fields(self):
        response = self.client.post('/login', json={
            'username': '',
            'password': ''
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()['message'], 'Missing username or password')

    @patch('login.mysql.connector.connect', side_effect=Exception("DB error"))
    def test_database_error(self, mock_connect):
        response = self.client.post('/login', json={
            'username': self.valid_username,
            'password': self.valid_password
        })

        self.assertEqual(response.status_code, 500)
        self.assertIn('Database error', response.get_json()['message'])

    @patch('login.mysql.connector.connect')
    def test_sql_injection_attempt(self, mock_connect):
        # Simulate no match for SQL injection input
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        response = self.client.post('/login', json={
            'username': "' OR 1=1 --",
            'password': "irrelevant"
        })

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()['message'], 'Invalid username or password')

if __name__ == '__main__':
    unittest.main()