from flask import jsonify, session
from database import get_connection, _safe_close

def setup_delete_appointment_route(app):
    @app.route("/appointments/<int:appointment_id>", methods=["DELETE"])
    def delete_appointment(appointment_id: int):
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointment_service WHERE Appointment_id=%s", (appointment_id,))
            cursor.execute("DELETE FROM appointment WHERE Appointment_id=%s", (appointment_id,))
            conn.commit()
            return jsonify({"status": "success", "message": "Appointment deleted"}), 200
        except Exception as err:
            if conn:
                conn.rollback()
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)