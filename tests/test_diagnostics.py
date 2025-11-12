import pytest
import json
from tests.conftest import client

class TestDiagnostics:
    """Diagnostic tests to identify 500 error causes"""
    
    def test_diagnose_signup_500(self, client):
        """Diagnose why signup returns 500"""
        response = client.post('/signup', json={
            'username': 'diagnostic_user',
            'email': 'diagnostic@example.com',
            'password': 'diagnostic_pass123'
        })
        
        print(f"\n=== SIGNUP DIAGNOSTIC ===")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Data: {response.data.decode()}")
        
        # This test is just for diagnostics, no assertion
    
    def test_diagnose_login_500(self, client):
        """Diagnose why login returns 500"""
        response = client.post('/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        print(f"\n=== LOGIN DIAGNOSTIC ===")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Data: {response.data.decode()}")
    
    def test_diagnose_book_500(self, authenticated_client):
        """Diagnose why booking returns 500"""
        response = authenticated_client.post('/book', json={
            'car_plate': 'DIAG123',
            'date': '2025-12-15',
            'time': '10:00',
            'service_ids': [1],
            'notes': 'Diagnostic appointment'
        })
        
        print(f"\n=== BOOK APPOINTMENT DIAGNOSTIC ===")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Data: {response.data.decode()}")