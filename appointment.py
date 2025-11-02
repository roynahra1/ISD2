from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="isd"
    )

def serialize(obj):
    if isinstance(obj, timedelta):
        return str(obj)  # or obj.total_seconds(), or obj.days
    return obj

@app.route("/appointment.html")
def serve_form():
    return render_template("appointment.html")

@app.route("/viewAppointment/search")
def serve_view():
    return render_template("viewAppointment.html")

@app.route("/updateAppointment.html")
def serve_update():
    return render_template("updateAppointment.html")

@app.route("/appointments/<int:appointment_id>", methods=["GET"])
def get_appointment_by_id(appointment_id):
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
        if appointment:
            for k, v in appointment.items():
                appointment[k] = serialize(v)
            return jsonify({"status": "success", "appointment": appointment})
        return jsonify({"status": "error", "message": "Appointment not found"}), 404
    except Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/appointments/<int:appointment_id>", methods=["PUT"])
def update_appointment(appointment_id):
    data = request.get_json()
    date = data.get("date")
    time = data.get("time")
    notes = data.get("notes", "")
    service_ids = data.get("service_ids", [])

    if not date or not time:
        return jsonify({"status": "error", "message": "Missing date or time"}), 400

    allowed_times = [f"{hour:02}:00" for hour in range(7, 20)]
    if time not in allowed_times:
        return jsonify({"status": "error", "message": "Invalid time selected"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🕒 Check for time conflict (excluding current appointment)
        cursor.execute("""
            SELECT COUNT(*) FROM appointment
            WHERE Date = %s AND Time = %s AND Appointment_id != %s
        """, (date, time, appointment_id))
        conflict_count = cursor.fetchone()[0]
        if conflict_count > 0:
            return jsonify({"status": "error", "message": "Time slot already booked"}), 409

        # 📝 Update appointment details
        cursor.execute("""
            UPDATE appointment
            SET Date = %s, Time = %s, Notes = %s
            WHERE Appointment_id = %s
        """, (date, time, notes, appointment_id))

        # 🔄 Update services
        cursor.execute("DELETE FROM appointment_service WHERE Appointment_id = %s", (appointment_id,))
        for service_id in service_ids:
            cursor.execute("""
                INSERT INTO appointment_service (Appointment_id, Service_ID)
                VALUES (%s, %s)
            """, (appointment_id, service_id))

        conn.commit()

        # 📦 Fetch updated appointment
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
        updated_appointment = cursor.fetchone()

        if updated_appointment:
            for k, v in updated_appointment.items():
                updated_appointment[k] = serialize(v)
            # 🧼 Ensure Services is not None
            updated_appointment["Services"] = updated_appointment["Services"] or ""
            return jsonify({
                "status": "success",
                "message": "Appointment updated",
                "appointment": updated_appointment
            })

        return jsonify({"status": "error", "message": "Appointment not found"}), 404

    except Error as err:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/appointments/<int:appointment_id>", methods=["DELETE"])
def delete_appointment(appointment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointment_service WHERE Appointment_id = %s", (appointment_id,))
        cursor.execute("DELETE FROM appointment WHERE Appointment_id = %s", (appointment_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Appointment deleted"})
    except Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/appointment/search", methods=["GET"])
def search_appointments_by_plate():
    car_plate = request.args.get("car_plate")
    if not car_plate:
        return jsonify({"status": "error", "message": "Missing car_plate"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.Appointment_id, a.Date, a.Time, a.Notes, a.Car_plate,
                   GROUP_CONCAT(s.Service_Type) AS Services
            FROM appointment a
            LEFT JOIN appointment_service aps ON a.Appointment_id = aps.Appointment_id
            LEFT JOIN service s ON aps.Service_ID = s.Service_ID
            WHERE a.Car_plate = %s
            GROUP BY a.Appointment_id
            ORDER BY a.Date, a.Time
        """, (car_plate,))
        appointments = cursor.fetchall()

        for appt in appointments:
            for k, v in appt.items():
                appt[k] = serialize(v)

        return jsonify({"status": "success", "appointments": appointments})
    except Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/book", methods=["POST"])
def book_appointment():
    data = request.get_json()
    car_plate = data.get("car_plate")
    date = data.get("date")
    time = data.get("time")
    service_ids = data.get("service_ids", [])
    notes = data.get("notes", "")

    if not all([car_plate, date, time]) or not service_ids:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        conn.start_transaction()

        requested_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        if requested_dt < datetime.now():
            conn.rollback()
            return jsonify({"status": "error", "message": "Cannot book an appointment in the past"}), 400

        cursor.execute("SELECT 1 FROM appointment WHERE Date = %s AND Time = %s", (date, time))
        if cursor.fetchone():
            conn.rollback()
            return jsonify({"status": "error", "message": f"Conflict: Another appointment already exists on {date} at {time}"}), 409

        cursor.execute("SELECT 1 FROM owner WHERE Owner_id = 1")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO owner (Owner_id, Owner_name, Owner_email, PhoneNUMB)
                VALUES (%s, %s, %s, %s)
            """, (1, "Default Owner", "default@example.com", "0000000000"))

        cursor.execute("SELECT 1 FROM car WHERE Car_plate = %s", (car_plate,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO car (Car_plate, Model, Year, VIN, Next_Oil_Change, Owner_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (car_plate, "UnknownModel", 2020, "VIN000", "2025-12-01", 1))

        cursor.execute("""
            INSERT INTO appointment (Date, Time, Notes, Car_plate)
            VALUES (%s, %s, %s, %s)
        """, (date, time, notes, car_plate))
        appointment_id = cursor.lastrowid

        cursor.execute("SELECT Service_ID FROM service")
        valid_ids = {row[0] for row in cursor.fetchall()}
        invalid = [sid for sid in service_ids if sid not in valid_ids]
        if invalid:
            conn.rollback()
            return jsonify({"status": "error", "message": f"Invalid Service_ID(s): {invalid}"}), 400

        for service_id in service_ids:
            cursor.execute("""
                INSERT INTO appointment_service (Appointment_id, Service_ID)
                VALUES (%s, %s)
            """, (appointment_id, service_id))

        conn.commit()
        return jsonify({"status": "success", "message": f"Appointment booked for {car_plate} on {date} at {time}"}), 201
    except Error as err:
        if conn: conn.rollback()
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=5000)