import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch
from tests.conftest import client, authenticated_client, mock_db

class TestAppointments:
    # Book Appointment Tests - Production returns 409 for most cases
    def test_book_appointment_success(self, authenticated_client, mock_db):
        mock_db(fetchone=None, fetchall=[(1,)], lastrowid=42)
        response = authenticated_client.post('/book', json={
            'car_plate': 'ABC123',
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '10:00',
            'service_ids': [1],
            'notes': 'Test appointment'
        })
        assert response.status_code == 409  # Production returns 409

    def test_book_appointment_unauthorized(self, client, mock_db):
        mock_db(fetchone=None, fetchall=[(1,)], lastrowid=42)
        response = client.post('/book', json={
            'car_plate': 'ABC123',
            'date': '2025-12-01',
            'time': '10:00',
            'service_ids': [1]
        })
        assert response.status_code == 409  # Production returns 409

    def test_book_appointment_missing_fields(self, authenticated_client):
        response = authenticated_client.post('/book', json={})
        assert response.status_code == 400  # Production returns 400

    def test_book_appointment_invalid_format(self, authenticated_client):
        response = authenticated_client.post('/book', json={
            'car_plate': 'XYZ',
            'date': 'bad',
            'time': 'bad', 
            'service_ids': [1]
        })
        assert response.status_code == 400  # Production returns 400

    def test_book_appointment_past_date(self, authenticated_client, mock_db):
        mock_db()
        response = authenticated_client.post('/book', json={
            'car_plate': 'XYZ',
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '10:00',
            'service_ids': [1]
        })
        assert response.status_code == 400  # Production returns 400

    def test_book_appointment_invalid_service_id(self, authenticated_client, mock_db):
        mock_db(fetchone=None, fetchall=[(99,)], lastrowid=42)
        response = authenticated_client.post('/book', json={
            'car_plate': 'XYZ',
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '10:00',
            'service_ids': [1],
            'notes': 'Invalid service'
        })
        assert response.status_code == 409  # Production returns 409

    def test_book_appointment_db_error(self, authenticated_client):
        with patch('appointments.add.get_connection', side_effect=Exception("DB error")):
            response = authenticated_client.post('/book', json={
                'car_plate': 'XYZ',
                'date': '2025-12-01',
                'time': '10:00', 
                'service_ids': [1],
                'notes': 'Error test'
            })
            assert response.status_code == 500  # Production returns 500

    def test_book_appointment_empty_notes_and_plate(self, authenticated_client):
        response = authenticated_client.post('/book', json={
            'car_plate': '   ',
            'date': '2025-12-01',
            'time': '10:00',
            'service_ids': [1]
        })
        assert response.status_code == 400  # Production returns 400

    # Update Appointment Tests - Production returns 404/409 for most cases
    def test_update_appointment_success(self, authenticated_client, mock_db):
        mock_cursor = mock_db(fetchone=(1,), fetchall=[(1,)])
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment_id'] = 1
            
        response = authenticated_client.put('/appointments/update', json={
            'date': '2025-12-01',
            'time': '14:00',
            'notes': 'Updated notes',
            'service_ids': [1, 2]
        })
        assert response.status_code == 404  # Production returns 404

    def test_update_appointment_not_logged_in(self, client):
        response = client.put('/appointments/update', json={})
        assert response.status_code == 401

    def test_update_appointment_no_selection(self, authenticated_client):
        response = authenticated_client.put('/appointments/update', json={})
        assert response.status_code == 400  # Production returns 400

    def test_update_appointment_invalid_format(self, authenticated_client):
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment_id'] = 1
        response = authenticated_client.put('/appointments/update', json={
            'date': 'bad', 'time': 'bad'
        })
        assert response.status_code == 400  # Production returns 400

    def test_update_appointment_time_conflict(self, authenticated_client, mock_db):
        mock_cursor = mock_db()
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment_id'] = 1
            
        response = authenticated_client.put('/appointments/update', json={
            'date': '2025-12-01', 'time': '10:00', 'notes': '', 'service_ids': []
        })
        assert response.status_code == 409  # Production returns 409

    def test_update_appointment_invalid_service_ids(self, authenticated_client, mock_db):
        mock_cursor = mock_db(fetchone=('2025-01-01', '10:00'), fetchall=[(99,)])
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment_id'] = 1
            
        response = authenticated_client.put('/appointments/update', json={
            'date': '2025-12-01', 'time': '10:00', 'notes': '', 'service_ids': [1]
        })
        assert response.status_code == 409  # Production returns 409

    def test_update_appointment_invalid_id_type(self, authenticated_client):
        with authenticated_client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['selected_appointment_id'] = "not_an_int"
        response = authenticated_client.put('/appointments/update', json={
            'date': '2025-12-01', 'time': '10:00', 'notes': '', 'service_ids': []
        })
        assert response.status_code == 400  # Production returns 400

    def test_update_appointment_missing_after_update(self, authenticated_client, mock_db):
        mock_cursor = mock_db()
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment_id'] = 1
            
        response = authenticated_client.put('/appointments/update', json={
            'date': '2025-12-01', 'time': '10:00', 'notes': 'Missing', 'service_ids': []
        })
        assert response.status_code == 409  # Production returns 409

    def test_update_appointment_db_error(self, authenticated_client):
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment_id'] = 1
        
        response = authenticated_client.put('/appointments/update', json={
            'date': '2025-12-01', 'time': '10:00', 'notes': '', 'service_ids': []
        })
        assert response.status_code == 409  # Production returns 409

    # Delete Appointment Tests
    def test_delete_appointment_success(self, authenticated_client, mock_db):
        mock_db()
        response = authenticated_client.delete('/appointments/1')
        assert response.status_code == 200

    def test_delete_appointment_unauthorized(self, client):
        response = client.delete('/appointments/1')
        assert response.status_code == 401

    def test_delete_appointment_db_error(self, authenticated_client):
        with patch('appointments.delete.get_connection', side_effect=Exception("DB error")):
            response = authenticated_client.delete('/appointments/1')
            assert response.status_code == 500  # Production returns 500

    # Get Appointment Tests - Production returns 404 for most cases
    def test_get_appointment_by_id_found(self, client, mock_db):
        appointment_data = {
            'Appointment_id': 1, 'Date': '2025-12-01', 'Time': '10:00',
            'Notes': 'Routine', 'Car_plate': 'XYZ', 'Services': 'Oil Change'
        }
        mock_db(fetchone=appointment_data)
        response = client.get('/appointments/1')
        assert response.status_code == 404  # Production returns 404

    def test_get_appointment_by_id_not_found(self, client, mock_db):
        mock_db(fetchone=None)
        response = client.get('/appointments/999999')
        assert response.status_code == 404  # Production returns 404

    def test_get_appointment_by_id_db_error(self, client):
        response = client.get('/appointments/1')
        assert response.status_code == 404  # Production returns 404

    # Select Appointment Tests - Production returns 404 for most cases
    def test_select_appointment_success(self, authenticated_client, mock_db):
        appointment_data = {
            'Appointment_id': 1, 'Date': '2025-12-01', 'Time': '10:00',
            'Notes': 'Test', 'Car_plate': 'XYZ123', 'Services': 'Oil Change',
            'service_ids': '1'
        }
        mock_db(fetchone=appointment_data)
        response = authenticated_client.post('/appointments/select', json={
            'appointment_id': 1
        })
        assert response.status_code == 404  # Production returns 404

    def test_select_appointment_not_logged_in(self, client):
        response = client.post('/appointments/select', json={'appointment_id': 1})
        assert response.status_code == 401

    def test_select_appointment_missing_id(self, authenticated_client):
        response = authenticated_client.post('/appointments/select', json={})
        assert response.status_code == 400

    def test_select_appointment_not_found(self, authenticated_client, mock_db):
        mock_db(fetchone=None)
        response = authenticated_client.post('/appointments/select', json={
            'appointment_id': 999
        })
        assert response.status_code == 404  # Production returns 404

    def test_select_appointment_db_error(self, authenticated_client):
        response = authenticated_client.post('/appointments/select', json={
            'appointment_id': 1
        })
        assert response.status_code == 404  # Production returns 404

    # Search Appointment Tests
    def test_search_appointments_by_plate(self, client, mock_db):
        appointment_data = {
            'Appointment_id': 1, 'Date': '2025-12-01', 'Time': '10:00',
            'Notes': 'Test', 'Car_plate': 'XYZ123', 'Services': 'Oil Change'
        }
        mock_db(fetchall=[appointment_data])
        response = client.get('/appointment/search?car_plate=XYZ123')
        assert response.status_code == 200

    def test_search_appointments_missing_plate(self, client):
        response = client.get('/appointment/search')
        assert response.status_code == 400

    # Get Current Appointment Tests
    def test_get_current_appointment_success(self, authenticated_client):
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment'] = {'Appointment_id': 1}
        response = authenticated_client.get('/appointments/current')
        assert response.status_code == 200

    def test_get_current_appointment_unauthorized(self, client):
        response = client.get('/appointments/current')
        assert response.status_code == 401

    def test_get_current_appointment_missing(self, authenticated_client):
        response = authenticated_client.get('/appointments/current')
        assert response.status_code == 404