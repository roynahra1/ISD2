from flask import jsonify
from database import get_connection, _safe_close, serialize

def setup_get_by_id_route(app):
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
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)