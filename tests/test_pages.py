import pytest
from tests.conftest import client, authenticated_client

class TestPages:
    def test_login_page(self, client):
        response = client.get('/login.html')
        assert response.status_code == 200

    def test_appointment_page(self, client):
        response = client.get('/appointment.html')
        assert response.status_code == 200

    def test_view_appointment_page(self, client):
        response = client.get('/viewAppointment/search')
        assert response.status_code == 200

    def test_signup_page(self, client):
        response = client.get('/signup.html')
        assert response.status_code == 200

    def test_update_appointment_page_redirects_when_not_logged_in(self, client):
        response = client.get('/updateAppointment.html')
        assert response.status_code == 302  # Redirect to login

    def test_update_appointment_page_redirects_when_no_selection(self, authenticated_client):
        response = authenticated_client.get('/updateAppointment.html')
        assert response.status_code == 302  # Redirect to search

    def test_update_appointment_page_success(self, authenticated_client):
        with authenticated_client.session_transaction() as sess:
            sess['selected_appointment'] = {'Appointment_id': 1}
        response = authenticated_client.get('/updateAppointment.html')
        assert response.status_code == 200