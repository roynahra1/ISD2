from flask import session, jsonify

def setup_status_route(app):
    @app.route("/auth/status", methods=["GET"])
    def auth_status():
        return jsonify({
            "status": "success",
            "logged_in": bool(session.get("logged_in")),
            "username": session.get("username")
        })