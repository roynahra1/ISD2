import unittest
from unittest.mock import patch, MagicMock
from appointment import app
from mysql.connector import Error
from datetime import datetime, timedelta

class TestBookAppointment(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.valid_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.valid_time = "10:00"
        self.valid_payload = {
            "car_plate": "ABC123",
            "date": self.valid_date,
            "time": self.valid_time,
            "service_ids": [1, 2],
            "notes": "Routine check"
        }

    @patch("appointment.get_connection")
    def test_missing_fields(self, mock_conn):
        payload = {"car_plate": "ABC123", "date": self.valid_date}
        response = self.client.post("/book", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.get_data(as_text=True))

    @patch("appointment.get_connection")
    def test_booking_in_past(self, mock_conn):
        conn = MagicMock()
        cursor = MagicMock()
        mock_conn.return_value = conn
        conn.cursor.return_value = cursor
        conn.start_transaction.return_value = None
        cursor.fetchone.side_effect = [None, None, None]

        payload = {
            "car_plate": "XYZ789",
            "date": "2000-01-01",
            "time": "10:00",
            "service_ids": [1],
            "notes": ""
        }
        response = self.client.post("/book", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot book an appointment in the past", response.get_data(as_text=True))

    @patch("appointment.get_connection")
    def test_conflicting_appointment(self, mock_conn):
        conn = MagicMock()
        cursor = MagicMock()
        mock_conn.return_value = conn
        conn.cursor.return_value = cursor
        conn.start_transaction.return_value = None
        cursor.fetchone.side_effect = [True]

        response = self.client.post("/book", json=self.valid_payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Conflict", response.get_data(as_text=True))

    @patch("appointment.get_connection")
    def test_invalid_service_id(self, mock_conn):
        conn = MagicMock()
        cursor = MagicMock()
        mock_conn.return_value = conn
        conn.cursor.return_value = cursor
        conn.start_transaction.return_value = None
        cursor.fetchone.side_effect = [
            None,  # no conflict
            None,  # owner does not exist
            None,  # car does not exist
            None   # service ID invalid
        ]

        payload = self.valid_payload.copy()
        payload["service_ids"] = [999]
        response = self.client.post("/book", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid Service_ID", response.get_data(as_text=True))

    @patch("appointment.get_connection")
    def test_successful_booking(self, mock_conn):
        conn = MagicMock()
        cursor = MagicMock()
        mock_conn.return_value = conn
        conn.cursor.return_value = cursor
        conn.start_transaction.return_value = None
        cursor.fetchone.side_effect = [
            None,  # no conflict
            True,  # owner exists
            True   # car exists
        ] + [True] * len(self.valid_payload["service_ids"])
        cursor.lastrowid = 123

        response = self.client.post("/book", json=self.valid_payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("Appointment booked", response.get_data(as_text=True))

    @patch("appointment.get_connection")
    def test_database_error(self, mock_conn):
        mock_conn.side_effect = Error("DB connection failed")
        response = self.client.post("/book", json=self.valid_payload)
        self.assertEqual(response.status_code, 500)
        self.assertIn("DB connection failed", response.get_data(as_text=True))

if __name__ == "__main__":
    unittest.main()