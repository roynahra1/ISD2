from flask import jsonify, session
from database import get_connection, _safe_close, serialize
from mysql.connector import Error
def setup_get_appointment_page(app):
    @app.route("/appointments/<int:appointment_id>", methods=["GET"])
    def get_appointment_by_id(appointment_id: int):
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
                WHERE a.Appointment_id = %s
                GROUP BY a.Appointment_id
            """, (appointment_id,))
            appointment = cursor.fetchone()
            if not appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404
            appointment = {k: serialize(v) for k, v in appointment.items()}
            return jsonify({"status": "success", "appointment": appointment}), 200
        except Error as err:
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)

    @app.route("/appointments/current", methods=["GET"])
    def get_current_appointment():
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        appointment = session.get("selected_appointment")
        if not appointment:
            return jsonify({"status": "error", "message": "No appointment selected"}), 404
        return jsonify({"status": "success", "appointment": appointment})