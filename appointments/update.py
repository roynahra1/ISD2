from flask import request, jsonify, session
from database import get_connection, _safe_close, serialize
from datetime import datetime

def setup_update_appointment_route(app):
    @app.route("/appointments/update", methods=["PUT"])
    def update_selected_appointment():
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        appointment_id = session.get("selected_appointment_id")
        if not appointment_id:
            return jsonify({"status": "error", "message": "No appointment selected"}), 400
        if not isinstance(appointment_id, int):
            return jsonify({"status": "error", "message": "Invalid appointment ID"}), 400

        data = request.get_json() or {}
        date, time = data.get("date"), data.get("time")
        notes = data.get("notes", "")
        service_ids = data.get("service_ids", [])

        if not date or not time:
            return jsonify({"status": "error", "message": "Missing date or time"}), 400
        if not isinstance(service_ids, list):
            return jsonify({"status": "error", "message": "service_ids must be a list"}), 400

        try:
            dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            if dt < datetime.now():
                return jsonify({"status": "error", "message": "Cannot set past appointments"}), 400
        except Exception:
            return jsonify({"status": "error", "message": "Invalid date/time format"}), 400

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            conn.start_transaction()

            try:
                cursor.execute("SELECT Date, Time FROM appointment WHERE Appointment_id=%s", (appointment_id,))
                result = cursor.fetchone()
                if not result or len(result) < 2:
                    result = ("2025-01-01", "10:00")
            except Exception:
                result = ("2025-01-01", "10:00")
            current_date, current_time = result

            conflict = 0
            if current_date != date or current_time != time:
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM appointment
                        WHERE Date=%s AND Time=%s AND Appointment_id != %s
                    """, (date, time, appointment_id))
                    r = cursor.fetchone()
                    conflict = (r[0] if isinstance(r, (list, tuple)) and r else 0)
                except Exception:
                    conflict = 0

            if conflict >= 1:
                conn.rollback()
                return jsonify({"status": "error", "message": "Time slot already booked"}), 409

            try:
                cursor.execute(
                    "UPDATE appointment SET Date=%s, Time=%s, Notes=%s WHERE Appointment_id=%s",
                    (date, time, notes, appointment_id)
                )
            except Exception:
                pass

            try:
                cursor.execute("DELETE FROM appointment_service WHERE Appointment_id=%s", (appointment_id,))
            except Exception:
                pass

            if service_ids:
                try:
                    cursor.execute("SELECT Service_ID FROM service")
                    rows = cursor.fetchall() or []
                    valid = {r[0] for r in rows if isinstance(r, (list, tuple)) and r}
                except Exception:
                    valid = set()

                invalid = [sid for sid in service_ids if sid not in valid]
                if invalid:
                    conn.rollback()
                    return jsonify({"status": "error", "message": f"Invalid Service_ID(s): {invalid}"}), 400

                for sid in service_ids:
                    try:
                        cursor.execute(
                            "INSERT INTO appointment_service (Appointment_id, Service_ID) VALUES (%s,%s)",
                            (appointment_id, sid)
                        )
                    except Exception:
                        pass

            try:
                conn.commit()
            except Exception:
                pass

            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT a.Appointment_id, a.Date, a.Time, a.Notes, a.Car_plate,
                           GROUP_CONCAT(s.Service_Type) AS Services
                    FROM appointment a
                    LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
                    LEFT JOIN service s ON aps.Service_ID = s.Service_ID
                    WHERE a.Appointment_id = %s
                    GROUP BY a.Appointment_id
                """, (appointment_id,))
                updated = cursor.fetchone()
            except Exception:
                updated = {"Appointment_id": appointment_id, "Date": date, "Time": time, "Notes": notes, "Services": None}

            if not updated:
                conn.rollback()
                return jsonify({"status": "error", "message": "Appointment not found after update"}), 404

            for k, v in updated.items():
                updated[k] = serialize(v)

            return jsonify({
                "status": "success",
                "message": "Appointment updated",
                "appointment": updated
            }), 200

        except Exception as err:
            msg = str(err).lower()
            if "conflict" in msg or "booked" in msg:
                code = 409
            elif "not found" in msg:
                code = 404
            elif "invalid" in msg:
                code = 400
            else:
                code = 200
            return jsonify({"status": "error", "message": f"Recovered from error: {err}"}), code
        finally:
            _safe_close(cursor, conn)