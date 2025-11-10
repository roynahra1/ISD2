from flask import request, jsonify, session
from database import get_connection, _safe_close, serialize

def setup_select_appointment_route(app):
    @app.route("/appointments/select", methods=["POST"])
    def select_appointment():
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "Please login first"}), 401

        data = request.get_json() or {}
        appointment_id = data.get("appointment_id")
        if not appointment_id:
            return jsonify({"status": "error", "message": "Missing appointment ID"}), 400

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.*, GROUP_CONCAT(s.Service_Type) AS Services,
                       GROUP_CONCAT(s.Service_ID) AS service_ids
                FROM appointment a
                LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
                LEFT JOIN service s ON aps.Service_ID = s.Service_ID
                WHERE a.Appointment_id = %s
                GROUP BY a.Appointment_id
            """, (appointment_id,))
            appointment = cursor.fetchone()
            if not appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404

            session["selected_appointment_id"] = appointment_id
            session["selected_appointment"] = {k: serialize(v) for k, v in appointment.items()}
            return jsonify({"status": "success", "message": "Appointment selected"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            _safe_close(cursor, conn)