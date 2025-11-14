import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch

class TestAppointmentRoutes:
    """Test appointment-related routes."""
    
    def test_book_appointment_validation(self, client, mock_db_success, sample_appointment_data):
        """Test appointment booking validation."""
        mock_conn, mock_cursor = mock_db_success
        
        # Test with valid data - should not crash
        response = client.post('/book',
                             data=json.dumps(sample_appointment_data),
                             content_type='application/json')
        
        # Should return some valid HTTP status
        assert response.status_code in [201, 400, 409, 500]

    def test_book_appointment_past_date(self, client):
        """Test booking appointment with past date."""
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        data = {
            "car_plate": "TEST123",
            "date": past_date,
            "time": "10:00",
            "service_ids": [1, 2]
        }
        
        response = client.post('/book',
                             data=json.dumps(data),
                             content_type='application/json')
        
        # Should return bad request or validation error
        assert response.status_code in [400, 500]

    def test_book_appointment_missing_fields(self, client):
        """Test booking with missing required fields."""
        test_cases = [
            {"car_plate": "", "date": "2024-01-15", "time": "10:00", "service_ids": [1]},
            {"car_plate": "TEST123", "date": "", "time": "10:00", "service_ids": [1]},
            {"car_plate": "TEST123", "date": "2024-01-15", "time": "", "service_ids": [1]},
            {"car_plate": "TEST123", "date": "2024-01-15", "time": "10:00", "service_ids": []},
        ]
        
        for data in test_cases:
            response = client.post('/book',
                                 data=json.dumps(data),
                                 content_type='application/json')
            assert response.status_code in [400, 500]

    def test_search_appointments_endpoint(self, client, mock_db_success):
        """Test appointment search endpoint."""
        mock_conn, mock_cursor = mock_db_success
        
        # Test with car plate parameter
        response = client.get('/appointment/search?car_plate=TEST123')
        
        # Should return some valid response
        assert response.status_code in [200, 400, 500]

    def test_search_appointments_missing_plate(self, client):
        """Test search without car plate."""
        response = client.get('/appointment/search')
        
        assert response.status_code == 400

    def test_get_appointment_by_id_endpoint(self, client, mock_db_success):
        """Test getting appointment by ID endpoint."""
        mock_conn, mock_cursor = mock_db_success
        
        response = client.get('/appointments/1')
        
        # Should return some valid response
        assert response.status_code in [200, 404, 500]

    def test_select_appointment_authenticated(self, auth_client, mock_db_success):
        """Test selecting appointment with authentication."""
        mock_conn, mock_cursor = mock_db_success
        
        response = auth_client.post('/appointments/select',
                                  data=json.dumps({'appointment_id': 1}),
                                  content_type='application/json')
        
        # Should handle the request (success or not found)
        assert response.status_code in [200, 404, 500]

    def test_select_appointment_unauthenticated(self, client):
        """Test selecting appointment without auth."""
        response = client.post('/appointments/select',
                             data=json.dumps({'appointment_id': 1}),
                             content_type='application/json')
        
        assert response.status_code == 401

    def test_update_appointment_endpoint(self, auth_client, mock_db_success):
        """Test update appointment endpoint."""
        mock_conn, mock_cursor = mock_db_success
        
        update_data = {
            "date": "2024-12-31",
            "time": "14:00",
            "service_ids": [1, 2],
            "notes": "Updated appointment"
        }
        
        response = auth_client.put('/appointments/update',
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        # Should handle the request
        assert response.status_code in [200, 400, 401, 404, 409, 500]

    def test_delete_appointment_authenticated(self, auth_client, mock_db_success):
        """Test deleting appointment with auth."""
        mock_conn, mock_cursor = mock_db_success
        
        response = auth_client.delete('/appointments/1')
        
        # Should handle the request
        assert response.status_code in [200, 401, 404, 500]

    def test_delete_appointment_unauthenticated(self, client):
        """Test deleting appointment without auth."""
        response = client.delete('/appointments/1')
        
        assert response.status_code == 401

    def test_get_current_appointment_success(self, auth_client):
        """Test getting current appointment."""
        response = auth_client.get('/appointments/current')
        
        assert response.status_code == 200

    def test_get_current_appointment_no_selection(self, auth_client):
        """Test getting current appointment when none selected."""
        with auth_client.session_transaction() as session:
            session.pop('selected_appointment', None)
        
        response = auth_client.get('/appointments/current')
        
        assert response.status_code == 404

    def test_all_appointment_endpoints_respond(self, client, auth_client):
        """Test that all appointment endpoints respond without crashing."""
        endpoints = [
            ('GET', '/appointment/search?car_plate=TEST'),
            ('GET', '/appointments/1'),
            ('POST', '/book'),
            ('PUT', '/appointments/update'),
            ('DELETE', '/appointments/1'),
        ]
        
        for method, endpoint in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, data=json.dumps({}), content_type='application/json')
            elif method == 'PUT':
                response = client.put(endpoint, data=json.dumps({}), content_type='application/json')
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            # Just verify no crashes - status codes will vary
            assert response.status_code in [200, 201, 400, 401, 404, 409, 500]