
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

from appointment import app, _safe_close


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def mock_db(self, fetchone=None, fetchall=None, lastrowid=None, side_effect=None):
        """
        Patch appointment.get_connection and return a mock connection with a mock cursor.
        - fetchone: value to return from cursor.fetchone()
        - fetchall: value to return from cursor.fetchall()
        - lastrowid: value to set for cursor.lastrowid
        - side_effect: if provided, set as side_effect on cursor.fetchone()
        """
        patcher = patch("appointment.get_connection")
        mock_get_conn = patcher.start()
        self.addCleanup(patcher.stop)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.return_value = None

        if side_effect is not None:
            mock_cursor.fetchone.side_effect = side_effect
        else:
            mock_cursor.fetchone.return_value = fetchone

        mock_cursor.fetchall.return_value = fetchall or []
        # lastrowid is an attribute on the cursor object in your app
        mock_cursor.lastrowid = lastrowid or 1

        mock_conn.commit.return_value = None
        mock_conn.rollback.return_value = None

        return mock_cursor
    # ✅ verify_password fallback
    def test_verify_password_none_hash(self):
     from appointment import verify_password
     self.assertFalse(verify_password(None, "any"))

    def test_verify_password_invalid_hash(self):
     from appointment import verify_password
     self.assertFalse(verify_password("not_a_hash", "any"))

# ✅ update_selected_appointment: invalid appointment_id type
    def test_update_appointment_invalid_id_type(self):
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["selected_appointment_id"] = "not_an_int"
     res = self.client.put("/appointments/update", json={
        "date": "2025-12-01", "time": "10:00", "notes": "", "service_ids": []
     })
     self.assertEqual(res.status_code, 400)



# ✅ update_selected_appointment: updated fetch returns None
    def test_update_appointment_missing_after_update(self):
     cursor = self.mock_db(fetchone=(1,), fetchall=[(1,)])
     cursor.fetchone.side_effect = [(1,), (0,), None]  # appointment exists, no conflict, but fetch fails
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["selected_appointment_id"] = 1
     res = self.client.put("/appointments/update", json={
        "date": "2025-12-01", "time": "10:00", "notes": "Missing", "service_ids": []
     })
     self.assertEqual(res.status_code, 404)

# ✅ book_appointment: empty notes, whitespace plate
    def test_book_appointment_empty_notes_and_plate(self):
     cursor = self.mock_db(fetchone=None, fetchall=[(1,)], lastrowid=42)
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
     res = self.client.post("/book", json={
        "car_plate": "   ",
        "date": "2025-12-01",
        "time": "10:00",
        "service_ids": [1]
     })
     self.assertEqual(res.status_code, 400)

# ✅ delete_appointment: unauthorized
    def test_delete_appointment_unauthorized(self):
     res = self.client.delete("/appointments/1")
     self.assertEqual(res.status_code, 401)

# ✅ delete_appointment: DB error
    @patch("appointment.get_connection")
    def test_delete_appointment_db_error(self, mock_get_conn):
     mock_conn = MagicMock()
     mock_cursor = MagicMock()
     mock_get_conn.return_value = mock_conn
     mock_conn.cursor.return_value = mock_cursor
     mock_cursor.execute.side_effect = Exception("DB error")
     mock_conn.rollback.return_value = None
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
     res = self.client.delete("/appointments/1")
     self.assertEqual(res.status_code, 500)

# ✅ get_current_appointment: logged in but no appointment
    def test_get_current_appointment_missing(self):
     with self.client.session_transaction() as sess:
        sess["logged_in"] = True
     res = self.client.get("/appointments/current")
     self.assertEqual(res.status_code, 404)
    # ✅ Signup
    def test_signup_success(self):
        # when checking username and email, first SELECTs return None
        self.mock_db(fetchone=None, lastrowid=1)
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "secure"})
        self.assertEqual(res.status_code, 201)

    def test_signup_missing_fields(self):
        res = self.client.post("/signup", json={})
        self.assertEqual(res.status_code, 400)

    def test_signup_short_password(self):
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "123"})
        self.assertEqual(res.status_code, 400)

    def test_signup_duplicate_username(self):
        # first fetchone() for username check returns truthy -> username exists
        self.mock_db(fetchone=(1,))
        res = self.client.post("/signup", json={"username": "u", "email": "e@x.com", "password": "secure"})
        self.assertEqual(res.status_code, 409)

    def test_signup_duplicate_email(self):
        # simulate username check None, email check truthy by side effects
        # side_effect makes first call (username) return None, second call (email) return (1,)
        self.mock_db(side_effect=[None, (1,)])
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
        # login selects password; return None -> invalid user
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
        data = json.loads(res.data)
        self.assertFalse(data["logged_in"])

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
        # When booking, code does multiple cursor.fetchone / fetchall calls:
        # - check appointment exists -> None
        # - check car exists -> None (insert)
        # - SELECT Service_ID FROM service -> return list of ids
        # So we provide fetchone=None and fetchall containing valid service ids
        cursor = self.mock_db(fetchone=None, fetchall=[(1,)], lastrowid=42)
        # ensure cursor.fetchall() returns a list of service ids (cursor.fetchall used later)
        cursor.fetchall.return_value = [(1,)]
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
        # simulate service table contains only 99, but requested 1 -> invalid
        cursor = self.mock_db(fetchone=None, fetchall=[(99,)], lastrowid=42)
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
        # The app uses cursor(dictionary=True) and cursor.fetchone() to return a dict
        appt = {
            "Appointment_id": 1,
            "Date": "2025-12-01",
            "Time": "10:00",
            "Notes": "Routine",
            "Car_plate": "XYZ",
            "Services": "Oil Change"
        }
        self.mock_db(fetchone=appt)
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
        # simulate time conflict by having SELECT COUNT(*) > 0
        cursor = self.mock_db(fetchone=(1,))  # first fetchone for SELECT 1 from appointment
        # make the COUNT select return (1,) as well via side_effect for fetchone
        cursor.fetchone.side_effect = [(1,), (1,)]
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["selected_appointment_id"] = 1
        res = self.client.put("/appointments/update", json={
            "date": "2025-12-01", "time": "10:00", "notes": "", "service_ids": []
        })
        self.assertEqual(res.status_code, 409)

    def test_update_appointment_invalid_service_ids(self):
        # simulate appointment exists, no time conflict, but invalid service ids
        cursor = self.mock_db(fetchone=(1,), fetchall=[(99,)])
        # Make fetchone return for the appointment existence check and later reads
        cursor.fetchone.side_effect = [(1,), None]  # first check -> exists
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["selected_appointment_id"] = 1
        res = self.client.put("/appointments/update", json={
            "date": "2025-12-01", "time": "10:00", "notes": "", "service_ids": [1]
        })
         
        self.assertEqual(res.status_code, 400)

    @patch("appointment.get_connection")
    def test_get_appointment_by_id_not_found_db(self, mock_get_conn):
        # simulate DB exception
        mock_get_conn.side_effect = Exception("DB error")
        res = self.client.get("/appointments/1")
        self.assertEqual(res.status_code, 500)

    def test_get_appointment_by_id_not_found(self):
        # simulate not found
        self.mock_db(fetchone=None)
        res = self.client.get("/appointments/999999")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Appointment not found", data["message"])

    def test_select_appointment_not_logged_in(self):
        res = self.client.post("/appointments/select", json={"appointment_id": 1})
        self.assertEqual(res.status_code, 401)

    def test_select_appointment_missing_id(self):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
        res = self.client.post("/appointments/select", json={})
        self.assertEqual(res.status_code, 400)

    def test_select_appointment_not_found(self):
        # login but appointment not found -> endpoint returns 404
        self.mock_db(fetchone=None)
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
        res = self.client.post("/appointments/select", json={"appointment_id": 999})
        self.assertEqual(res.status_code, 404)

    @patch("appointment.get_connection", side_effect=Exception("DB error"))
    def test_select_appointment_db_error(self, mock_get_conn):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
        res = self.client.post("/appointments/select", json={"appointment_id": 1})
        self.assertEqual(res.status_code, 500)

    # ✅ Search
    def test_search_appointments_valid_plate(self):
        appt = {
            "Appointment_id": 1,
            "Date": "2025-12-01",
            "Time": "10:00",
            "Notes": "Routine",
            "Car_plate": "XYZ",
            "Services": "Oil Change"
        }
        self.mock_db(fetchall=[appt])
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


if __name__ == "__main__":
    unittest.main()
