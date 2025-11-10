from flask import jsonify, session

def setup_logout_route(app):
    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return jsonify({"status": "success", "message": "Logged out"}), 200