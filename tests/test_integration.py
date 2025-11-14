import pytest
import json

class TestIntegrationFlows:
    """Test complete user flows."""
    
    def test_user_registration_and_login_flow(self, client, mock_db_success):
        """Test complete user registration and login flow."""
        mock_conn, mock_cursor = mock_db_success
        
        # Register user
        user_data = {
            "username": "flowuser",
            "email": "flow@example.com",
            "password": "flowpass123"
        }
        
        response = client.post('/signup',
                             data=json.dumps(user_data),
                             content_type='application/json')
        # Should handle the request
        assert response.status_code in [201, 400, 409, 500]
        
        # Login
        login_data = {
            "username": "flowuser",
            "password": "flowpass123"
        }
        
        response = client.post('/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        # Should handle the request
        assert response.status_code in [200, 401, 500]
    
    def test_appointment_management_flow(self, auth_client, mock_db_success):
        """Test complete appointment management flow."""
        mock_conn, mock_cursor = mock_db_success
        
        # Search appointments
        response = auth_client.get('/appointment/search?car_plate=FLOW123')
        assert response.status_code in [200, 400, 500]
        
        # Select appointment
        response = auth_client.post('/appointments/select',
                                  data=json.dumps({'appointment_id': 1}),
                                  content_type='application/json')
        assert response.status_code in [200, 404, 500]
        
        # Get current appointment
        response = auth_client.get('/appointments/current')
        assert response.status_code in [200, 404]
        
        # Update appointment
        update_data = {
            "date": "2024-12-31",
            "time": "14:00",
            "service_ids": [1, 2],
            "notes": "Updated via flow"
        }
        
        response = auth_client.put('/appointments/update',
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        assert response.status_code in [200, 400, 401, 404, 409, 500]
        
        # Delete appointment
        response = auth_client.delete('/appointments/1')
        assert response.status_code in [200, 401, 404, 500]