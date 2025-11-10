from flask import jsonify, session

def setup_get_current_route(app):
    @app.route("/appointments/current", methods=["GET"])
    def get_current_appointment():
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        appointment = session.get("selected_appointment")
        if not appointment:
            return jsonify({"status": "error", "message": "No appointment selected"}), 404
        return jsonify({"status": "success", "appointment": appointment})