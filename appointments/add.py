from flask import request, jsonify, session
from database import get_connection, _safe_close
from datetime import datetime

def setup_add_appointment_route(app):
    @app.route("/book", methods=["POST"])
    def book_appointment():
        # ADD THIS AUTH CHECK:
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "Please login first"}), 401

        data = request.get_json() or {}
        car_plate = (data.get("car_plate") or "").strip()
        date, time = data.get("date"), data.get("time")
        service_ids = data.get("service_ids", [])
        notes = data.get("notes", "")

        if not car_plate or not date or not time or not service_ids:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        if not isinstance(service_ids, list):
            return jsonify({"status": "error", "message": "service_ids must be a list"}), 400

        try:
            requested_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid date/time format"}), 400

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            conn.start_transaction()

            if requested_dt < datetime.now():
                return jsonify({"status": "error", "message": "Cannot book an appointment in the past"}), 400

            cursor.execute("SELECT 1 FROM appointment WHERE Date=%s AND Time=%s", (date, time))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Time slot already booked"}), 409

            cursor.execute("SELECT 1 FROM car WHERE Car_plate=%s", (car_plate,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO car (Car_plate, Model, Year, VIN, Next_Oil_Change, Owner_id)"
                    " VALUES (%s,%s,%s,%s,%s,%s)",
                    (car_plate, "Unknown", 2020, "VIN-UNKNOWN", None, 1)
                )

            cursor.execute("INSERT INTO appointment (Date, Time, Notes, Car_plate) VALUES (%s,%s,%s,%s)",
                          (date, time, notes, car_plate))
            appointment_id = cursor.lastrowid

            cursor.execute("SELECT Service_ID FROM service")
            valid_ids = {row[0] for row in (cursor.fetchall() or [])}
            invalid = [sid for sid in service_ids if sid not in valid_ids]
            if invalid:
                conn.rollback()
                return jsonify({"status": "error", "message": f"Invalid Service_ID(s): {invalid}"}), 400

            for sid in service_ids:
                cursor.execute("INSERT INTO appointment_service (Appointment_id, Service_ID) VALUES (%s,%s)",
                              (appointment_id, sid))
            conn.commit()
            return jsonify({"status": "success",
                            "message": f"Appointment booked for {car_plate}",
                            "appointment_id": appointment_id}), 201
        except Exception as err:
            if conn:
                conn.rollback()
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)