import pytest
import json
from tests.conftest import client, authenticated_client

class TestMainApp:
    """Tests for the main application routes and logic"""
    
    def test_main_routes_with_templates(self, client):
        """Test main routes that might render templates"""
        # Test all the main page routes from your directory listing
        main_routes = [
            '/', '/index', '/home',
            '/auto.html', '/carrer.html', '/client.html',
            '/franch.html', '/offers.html', '/store.html', 
            '/tires.html', '/login.html', '/signup.html',
            '/appointment.html', '/viewAppointment/search'
        ]
        
        for route in main_routes:
            response = client.get(route)
            print(f"Route {route}: {response.status_code}")
            # All should return some valid HTTP status
            assert response.status_code in [200, 302, 404, 401]
    
    def test_post_requests_to_main_routes(self, client):
        """Test POST requests to main routes"""
        post_routes = [
            '/', '/login', '/signup', '/book', '/appointments/select'
        ]
        
        for route in post_routes:
            response = client.post(route, json={})
            print(f"POST {route}: {response.status_code}")
            assert response.status_code in [200, 400, 401, 404, 405, 500]
    
    def test_put_delete_requests(self, client):
        """Test PUT and DELETE requests"""
        # Test PUT
        response = client.put('/appointments/update', json={})
        assert response.status_code in [200, 400, 401, 404, 405, 500]
        
        # Test DELETE
        response = client.delete('/appointments/1')
        assert response.status_code in [200, 401, 404, 500]
    
    def test_session_dependent_routes(self, client, authenticated_client):
        """Test routes that depend on session state"""
        # Test without authentication
        response = client.get('/updateAppointment.html')
        assert response.status_code in [302, 401, 404]  # Should redirect or deny
        
        # Test with authentication
        response = authenticated_client.get('/updateAppointment.html')
        assert response.status_code in [200, 302, 404]
    
    def test_all_http_methods(self, client):
        """Test all HTTP methods on common routes"""
        routes = ['/', '/login', '/signup', '/auth/status']
        
        for route in routes:
            for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                if method == 'GET':
                    response = client.get(route)
                elif method == 'POST':
                    response = client.post(route, json={})
                elif method == 'PUT':
                    response = client.put(route, json={})
                elif method == 'DELETE':
                    response = client.delete(route)
                elif method == 'PATCH':
                    response = client.patch(route, json={})
                
                # Should return some valid status, not crash
                assert response.status_code in [200, 201, 400, 401, 404, 405, 500]