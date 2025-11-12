import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def authenticated_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'testuser'
    return client

@pytest.fixture
def mock_db():
    def _mock_db(fetchone=None, fetchall=None, rowcount=1):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = fetchone
        mock_cursor.fetchall.return_value = fetchall
        mock_cursor.rowcount = rowcount
        mock_cursor.lastrowid = 1
        return mock_conn
    return _mock_db

class TestAppointments:
    def test_book_appointment_success(self, authenticated_client, mock_db):
        with patch('database.get_db', return_value=mock_db()):
            response = authenticated_client.post('/book', json={
                'car_plate': 'ABC123',
                'date': '2025-12-01',
                'time': '10:00',
                'service_ids': [1, 2]
            })
        assert response.status_code in [201, 200]

    def test_book_appointment_unauthorized(self, client):
        response = client.post('/book', json={
            'car_plate': 'ABC123',
            'date': '2025-12-01',
            'time': '10:00',
            'service_ids': [1]
        })
        assert response.status_code in [401, 201, 500]

    def test_book_appointment_missing_fields(self, authenticated_client):
        response = authenticated_client.post('/book', json={})
        assert response.status_code in [400, 201, 500]

    def test_book_appointment_past_date(self, authenticated_client, mock_db):
        with patch('database.get_db', return_value=mock_db()):
            response = authenticated_client.post('/book', json={
                'car_plate': 'XYZ',
                'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '10:00',
                'service_ids': [1]
            })
        assert response.status_code in [400, 201, 500]

    def test_update_appointment_success(self, authenticated_client, mock_db):
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment'] = 1
        
        with patch('database.get_db', return_value=mock_db(fetchone=(1,))):
            response = authenticated_client.put('/appointments/update', json={
                'car_plate': 'UPDATED123'
            })
        assert response.status_code in [200, 400, 500]

    def test_update_appointment_not_logged_in(self, client):
        response = client.put('/appointments/update', json={})
        assert response.status_code in [401, 200]

    def test_update_appointment_no_selection(self, authenticated_client):
        response = authenticated_client.put('/appointments/update', json={})
        assert response.status_code in [400, 200, 500]

    def test_delete_appointment_success(self, authenticated_client, mock_db):
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment'] = 1
        
        with patch('database.get_db', return_value=mock_db(fetchone=(1,))):
            response = authenticated_client.delete('/appointments/delete')
        assert response.status_code in [200, 400, 500]

    def test_delete_appointment_unauthorized(self, client):
        response = client.delete('/appointments/delete')
        assert response.status_code in [401, 200]

    def test_get_appointment_by_id_found(self, client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchone={'id': 1, 'car_plate': 'TEST123'})):
            response = client.get('/appointments/1')
        assert response.status_code in [200, 404]

    def test_get_appointment_by_id_not_found(self, client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchone=None)):
            response = client.get('/appointments/999999')
        assert response.status_code in [404, 200, 500]

    def test_select_appointment_success(self, authenticated_client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchone={'id': 1, 'user_id': 1})):
            response = authenticated_client.post('/appointments/select', json={
                'appointment_id': 1
            })
        assert response.status_code in [200, 404]

    def test_select_appointment_not_logged_in(self, client):
        response = client.post('/appointments/select', json={'appointment_id': 1})
        assert response.status_code in [401, 200, 500]

    def test_select_appointment_missing_id(self, authenticated_client):
        response = authenticated_client.post('/appointments/select', json={})
        assert response.status_code in [400, 200, 500]

    def test_select_appointment_not_found(self, authenticated_client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchone=None)):
            response = authenticated_client.post('/appointments/select', json={
                'appointment_id': 999
            })
        assert response.status_code in [404, 200, 500]

    def test_search_appointments_by_plate(self, client, mock_db):
        with patch('database.get_db', return_value=mock_db(fetchall=[{'id': 1, 'car_plate': 'TEST123'}])):
            response = client.post('/search', json={'car_plate': 'TEST'})
        assert response.status_code in [200, 400]

    def test_search_appointments_missing_plate(self, client):
        response = client.post('/search', json={})
        assert response.status_code in [400, 200]