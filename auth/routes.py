from flask import request, jsonify, session
from database import get_connection, _safe_close
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error
def setup_auth_routes(app):
    # ----------------------------
    # Authentication
    # ----------------------------
    @app.route("/signup", methods=["POST"])
    def signup():
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""

        if not username or not email or not password:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        if len(password) < 6:
            return jsonify({"status": "error", "message": "Password too short"}), 400

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM admin WHERE Username = %s", (username,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Username already exists"}), 409

            cursor.execute("SELECT 1 FROM admin WHERE Email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Email already registered"}), 409

            hashed = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO admin (Username, Email, Password) VALUES (%s, %s, %s)",
                (username, email, hashed)
            )
            conn.commit()
            return jsonify({"status": "success", "message": "Account created"}), 201

        except Error as err:
            if conn:
                conn.rollback()
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)

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
        except Error as err:
            return jsonify({"status": "error", "message": str(err)}), 500
        finally:
            _safe_close(cursor, conn)

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return jsonify({"status": "success", "message": "Logged out"}), 200

    @app.route("/auth/status", methods=["GET"])
    def auth_status():
        return jsonify({
            "status": "success",
            "logged_in": bool(session.get("logged_in")),
            "username": session.get("username")
        })