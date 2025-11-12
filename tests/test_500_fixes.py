import pytest
import json
from tests.conftest import client, authenticated_client

class Test500Fixes:
    """Tests to identify and fix 500 errors in specific endpoints"""
    
    def test_signup_endpoint_structure(self, client):
        """Test signup endpoint with different data structures"""
        # Test with valid data
        response = client.post('/signup', json={
            'username': 'testuser_fix',
            'email': 'test_fix@example.com',
            'password': 'password123'
        })
        print(f"Signup response: {response.status_code}")
        
        # Test with form data instead of JSON
        response = client.post('/signup', data={
            'username': 'testuser_fix2',
            'email': 'test_fix2@example.com',
            'password': 'password123'
        })
        print(f"Signup form data response: {response.status_code}")
    
    def test_login_endpoint_structure(self, client):
        """Test login endpoint with different data structures"""
        # Test with valid JSON
        response = client.post('/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        print(f"Login JSON response: {response.status_code}")
        
        # Test with form data
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        print(f"Login form data response: {response.status_code}")
    
    def test_book_endpoint_structure(self, authenticated_client):
        """Test book endpoint with different data structures"""
        # Test with valid JSON
        response = authenticated_client.post('/book', json={
            'car_plate': 'TEST500',
            'date': '2025-12-20',
            'time': '14:00',
            'service_ids': [1],
            'notes': 'Test fix'
        })
        print(f"Book JSON response: {response.status_code}")
        
        # Test with form data
        response = authenticated_client.post('/book', data={
            'car_plate': 'TEST500',
            'date': '2025-12-20',
            'time': '14:00',
            'service_ids': '[1]',  # Form data might send as string
            'notes': 'Test fix'
        })
        print(f"Book form data response: {response.status_code}")