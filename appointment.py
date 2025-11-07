# ...existing code...
import os
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict

from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app,supports_credentials=True, resources={
    r"/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": True
         }
     })


# configuration
app.secret_key = os.getenv("APP_SECRET_KEY", os.urandom(24))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # set to True in production when using HTTPS
    SESSION_COOKIE_SECURE=False
)

# DB config - adjust or use env vars in production
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "isd"),
    "auth_plugin": "mysql_native_password"
}


def get_connection():
    return mysql.connector.connect(**db_config)


#def sha1_hash(password: str) -> str:
    return hashlib.sha1(password.encode("utf-8")).hexdigest()


def verify_password(stored_hash: str | None, supplied: str) -> bool:
    """Verify password using Werkzeug's check_password_hash"""
    if not stored_hash:
        return False
    try:
        # Use only Werkzeug's secure hash checker
        return check_password_hash(stored_hash, supplied)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def serialize(val: Any) -> Any:
    if isinstance(val, (datetime, timedelta)):
        return str(val)
    return val


def _safe_close(cursor=None, conn=None):
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass
    try:
        if conn:
            conn.close()
    except Exception:
        pass


# -------------------------
# Template routes
# -------------------------
@app.route("/login.html")
def login_page():
    return render_template("login.html")


@app.route("/appointment.html")
def serve_form():
    return render_template("appointment.html")


@app.route("/viewAppointment/search")
def serve_view():
    return render_template("viewAppointment.html")


@app.route("/updateAppointment.html")
def serve_update():
    if not session.get("logged_in"):
        return redirect("/login.html")
    if not session.get("selected_appointment"):
        return redirect("/viewAppointment/search")
    return render_template("updateAppointment.html")

@app.route("/signup.html")
def signup_page():
    return render_template("signup.html")


# Remove or comment out these functions
# def generate_scrypt_hash(password: str) -> str:
#     ...def generate_scrypt_hash(password: str) -> str:
    import os
    import hashlib
    
    # Generate random salt
    salt = os.urandom(16).hex()
    
    # Further reduced memory parameters
    n = 8192  # Reduced from 16384
    r = 4     # Reduced from 8
    p = 1
    
    try:
        # Calculate hash with minimal parameters
        hash_value = hashlib.scrypt(
            password=password.encode(),
            salt=bytes.fromhex(salt),
            n=n,
            r=r,
            p=p,
            maxmem=1024 * 1024  # 1MB max memory
        ).hex()
        
        return f"scrypt:{n}:{r}:{p}${salt}${hash_value}"
    except ValueError as e:
        # Fallback to simple hash if memory issues persist
        print(f"Scrypt failed: {e}, falling back to SHA256")
        hash_value = hashlib.sha256(password.encode()).hexdigest()
        return f"sha256${salt}${hash_value}"


from werkzeug.security import generate_password_hash

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

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM admin WHERE Username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "Username already exists"}), 409

        cursor.execute("SELECT 1 FROM admin WHERE Email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "Email already registered"}), 409

        hashed = generate_password_hash(password)  # Uses pbkdf2:sha256 by default
        cursor.execute(
            "INSERT INTO admin (Username, Email, Password) VALUES (%s, %s, %s)",
            (username, email, hashed),
        )
        conn.commit()

        return jsonify({"status": "success", "message": "Account created"}), 201

    except Error as err:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        _safe_close(cursor, conn)
from werkzeug.security import check_password_hash

def verify_password(stored_hash, input_password):
    return check_password_hash(stored_hash, input_password)

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Password FROM admin WHERE Username = %s", (username,))
        row = cursor.fetchone()
        stored = row[0] if row else None

        print(f"Login attempt for user: {username}")
        print(f"Stored hash: {stored}")
        print(f"Supplied password: {password}")

        if stored and verify_password(stored, password):
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            session.permanent = True
            return jsonify({"status": "success", "message": "Login successful"}), 200

        print("Password verification failed")
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

    except Error as err:
        print(f"Login error: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        _safe_close(cursor, conn)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"}), 200


# -------------------------
# Appointment helpers / CRUD
# -------------------------
@app.route("/appointments/<int:appointment_id>", methods=["GET"])
def get_appointment_by_id(appointment_id: int):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.Appointment_id, a.Date, a.Time, a.Notes, a.Car_plate,
                   GROUP_CONCAT(s.Service_Type) AS Services
            FROM appointment a
            LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
            LEFT JOIN service s ON aps.Service_ID = s.Service_ID
            WHERE a.Appointment_id = %s
            GROUP BY a.Appointment_id
            """,
            (appointment_id,),
        )
        appointment = cursor.fetchone()
        if not appointment:
            return jsonify({"status": "error", "message": "Appointment not found"}), 404
        for k, v in appointment.items():
            appointment[k] = serialize(v)
        return jsonify({"status": "success", "appointment": appointment}), 200
    except Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        _safe_close(cursor, conn)


# store selected appointment id in session (admin selects an appointment to update)
# Replace or update the existing select_appointment route

# Add this new route

@app.route("/auth/status", methods=["GET"])
def auth_status():
    return jsonify({
        "status": "success",
        "logged_in": bool(session.get("logged_in")),
        "username": session.get("username")
    })
     
# Update the select_appointment route

@app.route("/appointments/select", methods=["POST"])
def select_appointment():
    # Check login status first
    if not session.get("logged_in"):
        return jsonify({
            "status": "error",
            "message": "Please login first"
        }), 401

    data = request.get_json() or {}
    appointment_id = data.get("appointment_id")
    
    if not appointment_id:
        return jsonify({"status": "error", "message": "Missing appointment ID"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT a.*, GROUP_CONCAT(s.Service_Type) as Services,
                   GROUP_CONCAT(s.Service_ID) as service_ids
            FROM appointment a
            LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
            LEFT JOIN service s ON aps.Service_ID = s.Service_ID
            WHERE a.Appointment_id = %s
            GROUP BY a.Appointment_id
        """, (appointment_id,))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            return jsonify({"status": "error", "message": "Appointment not found"}), 404

        # Store in session
        session['selected_appointment_id'] = appointment_id
        session['selected_appointment'] = {k: serialize(v) for k, v in appointment.items()}
        
        return jsonify({
            "status": "success",
            "message": "Appointment selected"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        _safe_close(cursor, conn)        
 

@app.route("/appointments/update", methods=["PUT"])
def update_selected_appointment():
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Get appointment ID from session
    appointment_id = session.get("selected_appointment_id")
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment selected"}), 400

    data = request.get_json() or {}
    date = data.get("date")
    time = data.get("time")
    
    # Validate date/time not in past
    try:
        date_time_str = f"{date} {time}"
        appointment_datetime = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
        if appointment_datetime < datetime.now():
            return jsonify({
                "status": "error",
                "message": "Cannot set appointment date/time in the past"
            }), 400
    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid date/time format"
        }), 400

    notes = data.get("notes", "")
    service_ids = data.get("service_ids", [])

    if not date or not time:
        return jsonify({"status": "error", "message": "Missing date or time"}), 400

    # validate date/time format
    try:
        datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date/time format"}), 400

    if not isinstance(service_ids, list):
        return jsonify({"status": "error", "message": "service_ids must be a list"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        conn.start_transaction()

        # ensure appointment exists
        cursor.execute("SELECT 1 FROM appointment WHERE Appointment_id = %s", (appointment_id,))
        if not cursor.fetchone():
            conn.rollback()
            return jsonify({"status": "error", "message": "Appointment not found"}), 404

        # check for time conflict (exclude current appointment)
        cursor.execute(
            "SELECT COUNT(*) FROM appointment WHERE Date = %s AND Time = %s AND Appointment_id != %s",
            (date, time, appointment_id),
        )
        if cursor.fetchone()[0] > 0:
            conn.rollback()
            return jsonify({"status": "error", "message": "Time slot already booked"}), 409

        # update appointment
        cursor.execute(
            "UPDATE appointment SET Date = %s, Time = %s, Notes = %s WHERE Appointment_id = %s",
            (date, time, notes, appointment_id),
        )

        # replace services: delete existing then insert provided ones (validate ids)
        cursor.execute("DELETE FROM appointment_service WHERE Appointment_id = %s", (appointment_id,))
        if service_ids:
            cursor.execute("SELECT Service_ID FROM service")
            valid_ids = {row[0] for row in cursor.fetchall()}
            invalid = [sid for sid in service_ids if sid not in valid_ids]
            if invalid:
                conn.rollback()
                return jsonify({"status": "error", "message": f"Invalid Service_ID(s): {invalid}"}), 400
            for sid in service_ids:
                cursor.execute(
                    "INSERT INTO appointment_service (Appointment_id, Service_ID) VALUES (%s, %s)",
                    (appointment_id, sid),
                )

        conn.commit()

        # fetch updated appointment
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.Appointment_id, a.Date, a.Time, a.Notes, a.Car_plate,
                   GROUP_CONCAT(s.Service_Type) AS Services
            FROM appointment a
            LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
            LEFT JOIN service s ON aps.Service_ID = s.Service_ID
            WHERE a.Appointment_id = %s
            GROUP BY a.Appointment_id
            """,
            (appointment_id,),
        )
        updated = cursor.fetchone()
        if not updated:
            return jsonify({"status": "error", "message": "Appointment not found after update"}), 404
        for k, v in updated.items():
            updated[k] = serialize(v)
        updated["Services"] = updated.get("Services") or ""
        return jsonify({"status": "success", "message": "Appointment updated", "appointment": updated}), 200

    except Error as err:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        _safe_close(cursor, conn)


@app.route("/appointments/<int:appointment_id>", methods=["DELETE"])
def delete_appointment(appointment_id: int):
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointment_service WHERE Appointment_id = %s", (appointment_id,))
        cursor.execute("DELETE FROM appointment WHERE Appointment_id = %s", (appointment_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Appointment deleted"}), 200
    except Error as err:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        _safe_close(cursor, conn)


@app.route("/appointment/search", methods=["GET"])
def search_appointments_by_plate():
    car_plate = request.args.get("car_plate")
    if not car_plate:
        return jsonify({"status": "error", "message": "Missing car_plate"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.Appointment_id, a.Date, a.Time, a.Notes, a.Car_plate,
                   GROUP_CONCAT(s.Service_Type) AS Services
            FROM appointment a
            LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
            LEFT JOIN service s ON aps.Service_ID = s.Service_ID
            WHERE a.Car_plate = %s
            GROUP BY a.Appointment_id
            ORDER BY a.Date, a.Time
            """,
            (car_plate,),
        )
        appointments = cursor.fetchall()
        for appt in appointments:
            for k, v in appt.items():
                appt[k] = serialize(v)
        return jsonify({"status": "success", "appointments": appointments}), 200
    except Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        _safe_close(cursor, conn)


@app.route("/book", methods=["POST"])
def book_appointment():
    data = request.get_json() or {}
    car_plate = (data.get("car_plate") or "").strip()
    date = data.get("date")
    time = data.get("time")
    service_ids = data.get("service_ids", [])
    notes = data.get("notes", "")

    if not car_plate or not date or not time or not service_ids:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    if not isinstance(service_ids, list):
        return jsonify({"status": "error", "message": "service_ids must be a list"}), 400

    try:
        requested_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date/time format"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        conn.start_transaction()

        if requested_dt < datetime.now():
            conn.rollback()
            return jsonify({"status": "error", "message": "Cannot book an appointment in the past"}), 400

        cursor.execute("SELECT 1 FROM appointment WHERE Date = %s AND Time = %s", (date, time))
        if cursor.fetchone():
            conn.rollback()
            return jsonify({"status": "error", "message": "Time slot already booked"}), 409

        # Ensure car exists, create minimal if not (adjust to your schema & validation)
        cursor.execute("SELECT 1 FROM car WHERE Car_plate = %s", (car_plate,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO car (Car_plate, Model, Year, VIN, Next_Oil_Change, Owner_id) VALUES (%s,%s,%s,%s,%s,%s)",
                (car_plate, "Unknown", 2020, "VIN-UNKNOWN", None, 1),
            )

        # insert appointment
        cursor.execute(
            "INSERT INTO appointment (Date, Time, Notes, Car_plate) VALUES (%s, %s, %s, %s)",
            (date, time, notes, car_plate),
        )
        appointment_id = cursor.lastrowid

        # validate service ids
        cursor.execute("SELECT Service_ID FROM service")
        valid_ids = {row[0] for row in cursor.fetchall()}
        invalid = [sid for sid in service_ids if sid not in valid_ids]
        if invalid:
            conn.rollback()
            return jsonify({"status": "error", "message": f"Invalid Service_ID(s): {invalid}"}), 400

        for sid in service_ids:
            cursor.execute(
                "INSERT INTO appointment_service (Appointment_id, Service_ID) VALUES (%s, %s)",
                (appointment_id, sid),
            )

        conn.commit()
        return jsonify(
            {"status": "success", "message": f"Appointment booked for {car_plate} on {date} at {time}", "appointment_id": appointment_id}
        ), 201
    except Error as err:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        _safe_close(cursor, conn)


# Add this new route

@app.route("/appointments/current", methods=["GET"])
def get_current_appointment():
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    appointment = session.get("selected_appointment")
    if not appointment:
        return jsonify({"status": "error", "message": "No appointment selected"}), 404
        
    return jsonify({
        "status": "success",
        "appointment": appointment
    })


if __name__ == "__main__":
    print("Server starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0',port=5000)