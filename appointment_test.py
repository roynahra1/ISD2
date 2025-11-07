import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json
import importlib

from appointment import app, _safe_close


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def mock_db(self, fetchone=None, fetchall=None, lastrowid=None, side_effect=None):
        patcher = patch("appointment.get_connection")
        mock_db = patcher.start()
        self.addCleanup(patcher.stop)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.side_effect = side_effect or fetchone
        mock_cursor.fetchall.return_value = fetchall or []
        mock_cursor.lastrowid = lastrowid or 1
        mock_conn.commit.return_value = None
        mock_conn.rollback.return_value = None

        return mock_cursor

    # ✅ Signup
    def test_signup_success(self):
        self.mock_db(fetchone=[None, None])
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "secure"})
        self.assertEqual(res.status_code, 201)

    def test_signup_missing_fields(self):
        res = self.client.post("/signup", json={})
        self.assertEqual(res.status_code, 400)

    def test_signup_short_password(self):
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "123"})
        self.assertEqual(res.status_code, 400)

    def test_signup_duplicate_username(self):
        self.mock_db(fetchone=[True])
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "secure"})
        self.assertEqual(res.status_code, 409)

    def test_signup_duplicate_email(self):
        self.mock_db(fetchone=[None, True])
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "secure"})
        self.assertEqual(res.status_code, 409)

    def test_signup_db_error(self):
        patcher = patch("appointment.get_connection")
        mock_get_conn = patcher.start()
        self.addCleanup(patcher.stop)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_conn.rollback.return_value = None
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "secure"})
        self.assertEqual(res.status_code, 500)

    # ✅ Login
    def test_login_invalid_user(self):
        self.mock_db(fetchone=None)
        res = self.client.post("/login", json={"username": "ghost", "password": "wrong"})
        self.assertEqual(res.status_code, 401)

    def test_login_missing_fields(self):
        res = self.client.post("/login", json={})
        self.assertEqual(res.status_code, 400)

    def test_logout(self):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
        res = self.client.post("/logout")
        self.assertEqual(res.status_code, 200)

    def test_auth_status_logged_out(self):
        res = self.client.get("/auth/status")
        self.assertFalse(json.loads(res.data)["logged_in"])

    def test_auth_status_logged_in(self):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["username"] = "u"
        res = self.client.get("/auth/status")
        self.assertEqual(res.status_code, 200)

    def test_auth_status_contains_username(self):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["username"] = "Roy"
        res = self.client.get("/auth/status")
        data = json.loads(res.data)
        self.assertTrue(data["logged_in"])
        self.assertEqual(data["username"], "Roy")

    # ✅ Booking
    def test_book_appointment_missing_fields(self):
        res = self.client.post("/book", json={})
        self.assertEqual(res.status_code, 400)

    def test_book_appointment_invalid_format(self):
        res = self.client.post("/book", json={
            "car_plate": "XYZ",
            "date": "bad",
            "time": "bad",
            "service_ids": [1]
        })
        self.assertEqual(res.status_code, 400)

    def test_book_appointment_past_date(self):
        self.mock_db()
        res = self.client.post("/book", json={
            "car_plate": "XYZ",
            "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "10:00",
            "service_ids": [1]
        })
        self.assertEqual(res.status_code, 400)

    def test_book_appointment_success(self):
        self.mock_db(fetchone=[None, None, None], fetchall=[(1,), (1,)], lastrowid=42)
        res = self.client.post("/book", json={
            "car_plate": "XYZ",
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "10:00",
            "service_ids": [1],
            "notes": "Routine"
        })
        self.assertEqual(res.status_code, 201)

    @patch("appointment.get_connection")
    def test_book_appointment_db_error(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_conn.rollback.return_value = None
        res = self.client.post("/book", json={
            "car_plate": "XYZ",
            "date": "2025-12-01",
            "time": "10:00",
            "service_ids": [1],
            "notes": "Error test"
        })
        self.assertEqual(res.status_code, 500)

    def test_book_appointment_invalid_service_id(self):
        self.mock_db(fetchone=[None, None, None], fetchall=[(99,)], lastrowid=42)
        res = self.client.post("/book", json={
            "car_plate": "XYZ",
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "10:00",
            "service_ids": [1],
            "notes": "Invalid service"
        })
        self.assertEqual(res.status_code, 400)

    # ✅ Get appointment
    def test_get_appointment_by_id_found(self):
        self.mock_db(fetchone=({
            "Appointment_id": 1,
            "Date": "2025-12-01",
            "Time": "10:00",
            "Notes": "Routine",
            "Car_plate": "XYZ",
            "Services": "Oil Change"
        },))
        res = self.client.get("/appointments/1")
        self.assertEqual(res.status_code, 200)
    
    def test_update_appointment_not_logged_in(self):
      res = self.client.put("/appointments/update", json={})
      self.assertEqual(res.status_code, 401)

    def test_update_appointment_no_selection(self):
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
     res = self.client.put("/appointments/update", json={})
     self.assertEqual(res.status_code, 400)

    def test_update_appointment_invalid_format(self):
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["selected_appointment_id"] = 1
     res = self.client.put("/appointments/update", json={"date": "bad", "time": "bad"})
     self.assertEqual(res.status_code, 400)

    def test_update_appointment_time_conflict(self):
     cursor = self.mock_db(fetchone=[True, [1]])
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["selected_appointment_id"] = 1
     res = self.client.put("/appointments/update", json={
        "date": "2025-12-01", "time": "10:00", "notes": "", "service_ids": []
     })
     self.assertEqual(res.status_code, 409)

    def test_update_appointment_invalid_service_ids(self):
     cursor = self.mock_db(fetchone=[True, [0]], fetchall=[(99,)])  # 99 is valid, 1 is not
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["selected_appointment_id"] = 1
     res = self.client.put("/appointments/update", json={
        "date": "2025-12-01", "time": "10:00", "notes": "", "service_ids": [1]
     })
     self.assertEqual(res.status_code, 400)

     
    @patch("appointment.get_connection")
    def test_get_appointment_by_id_not_found(self, mock_get_conn):
      mock_cursor = MagicMock()
      mock_cursor.fetchone.return_value = None
      mock_get_conn.return_value.cursor.return_value = mock_cursor

      with self.client as client:
        res = client.get("/appointments/999999")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Appointment not found", data["message"])

    @patch("appointment.get_connection", side_effect=Exception("DB error"))
    def test_get_appointment_by_id_db_error(self, mock_get_conn):
        res = self.client.get("/appointments/1")
        self.assertEqual(res.status_code, 500)
    def test_select_appointment_not_logged_in(self):
     res = self.client.post("/appointments/select", json={"appointment_id": 1})
     self.assertEqual(res.status_code, 401)

    def test_select_appointment_missing_id(self):
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
     res = self.client.post("/appointments/select", json={})
     self.assertEqual(res.status_code, 400)

    def test_select_appointment_not_found(self):
      self.mock_db(fetchone=None)
      with self.client.session_transaction() as sess:
        sess["logged_in"] = True
      res = self.client.post("/appointments/select", json={"appointment_id": 999})
      self.assertEqual(res.status_code, 200)

    @patch("appointment.get_connection", side_effect=Exception("DB error"))
    def test_select_appointment_db_error(self, mock_get_conn):
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
     res = self.client.post("/appointments/select", json={"appointment_id": 1})
     self.assertEqual(res.status_code, 500)
    # ✅ Search
    def test_search_appointments_valid_plate(self):
        self.mock_db(fetchall=[{
            "Appointment_id": 1,
            "Date": "2025-12-01",
            "Time": "10:00",
            "Notes": "Routine",
            "Car_plate": "XYZ",
            "Services": "Oil Change"
        }])
        res = self.client.get("/appointment/search?car_plate=XYZ")
        self.assertEqual(res.status_code, 200)

    def test_search_appointments_missing_plate(self):
        res = self.client.get("/appointment/search")
        self.assertEqual(res.status_code, 400)

    # ✅ Template routes
    def test_template_routes(self):
        for route in ["/login.html", "/appointment.html", "/viewAppointment/search", "/signup.html"]:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200)

    def test_update_appointment_page_redirects(self):
        res = self.client.get("/updateAppointment.html")
        self.assertEqual(res.status_code, 302)
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
        res = self.client.get("/updateAppointment.html")
        self.assertEqual(res.status_code, 302)
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["selected_appointment"] = {"Appointment_id": 1}
        res = self.client.get("/updateAppointment.html")
        self.assertEqual(res.status_code, 200)

    # ✅ Safe close
    def test_safe_close(self):
        _safe_close()  # Should not raise

    def test_safe_close_with_exceptions(self):
        class BadObj:
            def close(self): raise Exception("fail")
        _safe_close(BadObj(), BadObj())

    # ✅ scrypt fallback
   
    

if __name__ == "__main__":
    unittest.main()
