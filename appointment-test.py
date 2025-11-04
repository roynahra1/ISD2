import unittest
from datetime import datetime, timedelta
import json
from appointment import app
from unittest.mock import patch, MagicMock

TEST_CONFIG = {
    'TESTING': True,
    'DEBUG': False,
    'PRESERVE_CONTEXT_ON_EXCEPTION': False
}

class TestAppointmentAPI(unittest.TestCase):
    def setUp(self):
        """Set up test client and mock session"""
        self.app = app.test_client()
        self.app.testing = True
        # Mock session for logged in state
        self.session_patch = patch('appointment.session', {
            'logged_in': True,
            'username': 'testuser',
            'selected_appointment_id': 1
        })
        self.session_patch.start()

    def tearDown(self):
        """Clean up patches"""
        self.session_patch.stop()

    def create_test_appointment_data(self, days_ahead=1):
        """Helper method to create test appointment data"""
        return {
            "car_plate": "A12345",
            "date": (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d'),
            "time": "14:00",
            "service_ids": [1, 2],
            "notes": "Test appointment"
        }

    def test_book_appointment_success(self):
        """Test successful appointment booking"""
        data = {
            "car_plate": "A12345",
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "time": "14:00",
            "service_ids": [1, 2],
            "notes": "Test appointment"
        }

        with patch('appointment.get_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_db.return_value.cursor.return_value = mock_cursor
            # Mock responses in correct order
            mock_cursor.fetchone.side_effect = [
                None,  # Time slot check
                None,  # Car exists check
            ]
            mock_cursor.fetchall.return_value = [(1,), (2,)]  # Valid service IDs
            mock_cursor.lastrowid = 1

            response = self.app.post('/book',
                                   data=json.dumps(data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 201)
            response_data = json.loads(response.data)
            self.assertEqual(response_data['status'], 'success')

    def test_invalid_car_plate(self):
        """Test booking with invalid car plate format"""
        data = {
            "car_plate": "123456",  # Invalid: doesn't start with letter
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "time": "14:00",
            "service_ids": [1]
        }

        with patch('appointment.get_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_db.return_value.cursor.return_value = mock_cursor
            # Don't need to mock DB responses as validation should fail first
            mock_cursor.fetchone.return_value = None

            response = self.app.post('/book',
                               data=json.dumps(data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')

    def test_update_appointment(self):
        """Test updating an appointment"""
        data = {
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "time": "15:00",
            "service_ids": [1, 3],
            "notes": "Updated notes"
        }

        with patch('appointment.get_connection') as mock_db, \
             patch('appointment.session', {
                 'logged_in': True,
                 'username': 'testuser',
                 'selected_appointment_id': 1,
                 'selected_appointment': {'Appointment_id': 1}
             }):
            mock_cursor = MagicMock()
            mock_db.return_value.cursor.return_value = mock_cursor
            
            # Mock responses in correct order
            mock_cursor.fetchone.side_effect = [
                {'Appointment_id': 1},  # Appointment exists check
                (0,),                   # Time conflict check (returns tuple)
                {'Appointment_id': 1,    # Final appointment fetch
                 'Date': data['date'],
                 'Time': data['time'],
                 'Notes': data['notes'],
                 'Car_plate': 'A12345',
                 'Services': 'Service1,Service2'}
            ]
            mock_cursor.fetchall.return_value = [(1,), (3,)]  # Valid service IDs

            response = self.app.put('/appointments/update',
                                  data=json.dumps(data),
                                  content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data)
            self.assertEqual(response_data['status'], 'success')

    def test_search_appointments(self):
        """Test searching appointments by car plate"""
        with patch('appointment.get_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_db.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [{
                'Appointment_id': 1,
                'Date': '2025-11-05',
                'Time': '14:00:00',
                'Car_plate': 'A12345',
                'Notes': 'Test',
                'Services': 'Oil Change,Tire Rotation'
            }]

            response = self.app.get('/appointment/search?car_plate=A12345')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data)
            self.assertEqual(response_data['status'], 'success')
            self.assertEqual(len(response_data['appointments']), 1)

    def test_time_slot_conflict(self):
        """Test booking when time slot is already taken"""
        data = {
            "car_plate": "A12345",
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "time": "14:00",
            "service_ids": [1]
        }

        with patch('appointment.get_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_db.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (1,)  # Time slot taken

            response = self.app.post('/book',
                                   data=json.dumps(data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 409)
            response_data = json.loads(response.data)
            self.assertEqual(response_data['status'], 'error')
            self.assertIn('already booked', response_data['message'])

    def test_authentication_required(self):
        """Test endpoints requiring authentication"""
        with patch('appointment.session', {}):  # No login
            response = self.app.put('/appointments/update')
            self.assertEqual(response.status_code, 401)

    def test_date_validation(self):
        """Test past date rejection"""
        data = self.create_test_appointment_data(days_ahead=-1)
        response = self.app.post('/book', 
                           data=json.dumps(data),
                           content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_car_plate_number_only(self):
        """Test booking with car plate that doesn't start with letter"""
        data = self.create_test_appointment_data()
        data["car_plate"] = "123456"
        
        response = self.app.post('/book',
                           data=json.dumps(data),
                           content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('must start with a letter', response_data['message'])

    def test_invalid_car_plate_too_short(self):
        """Test booking with car plate that's too short"""
        data = self.create_test_appointment_data()
        data["car_plate"] = "A"
        
        response = self.app.post('/book',
                           data=json.dumps(data),
                           content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('too short', response_data['message'])

    def test_invalid_car_plate_too_long(self):
        """Test booking with car plate that's too long"""
        data = self.create_test_appointment_data()
        data["car_plate"] = "A1234567"
        
        response = self.app.post('/book',
                           data=json.dumps(data),
                           content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('too long', response_data['message'])

if __name__ == '__main__':
    unittest.main()