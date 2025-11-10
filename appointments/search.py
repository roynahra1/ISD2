from flask import request, jsonify
from database import get_connection, _safe_close, serialize

def setup_search_appointment_route(app):
    @app.route("/appointment/search", methods=["GET"])
    def search_appointments_by_plate():
        car_plate = request.args.get("car_plate")
        if not car_plate:
            return jsonify({"status": "error", "message": "Missing car_plate"}), 400

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.Appointment_id, a.Date, a.Time, a.Notes, a.Car_plate,
                       GROUP_CONCAT(s.Service_Type) AS Services
                FROM appointment a
                LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
                LEFT JOIN service s ON aps.Service_ID = s.Service_ID
                WHERE a.Car_plate = %s
                GROUP BY a.Appointment_id
                ORDER BY a.Date, a.Time
            """, (car_plate,))
            appointments = cursor.fetchall()
            for appt in appointments:
                for k, v in appt.items():
                    appt[k] = serialize(v)
            return jsonify({"status": "success", "appointments": appointments}), 200
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)