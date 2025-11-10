from flask import request, jsonify, session
from database import get_connection, _safe_close
from werkzeug.security import check_password_hash
from mysql.connector import Error
def setup_login_route(app):
    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"status": "error", "message": "Missing username or password"}), 400

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Password FROM admin WHERE Username = %s", (username,))
            row = cursor.fetchone()
            if row and check_password_hash(row[0], password):
                session.clear()
                session.update({"logged_in": True, "username": username})
                session.permanent = True
                return jsonify({"status": "success", "message": "Login successful"}), 200
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)