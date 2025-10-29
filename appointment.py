from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route("/appointment.html")
def serve_form():
    return render_template("appointment.html")  # Ensure this file is in /templates

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="isd"
    )


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

        # Prevent booking in the past
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        requested = f"{date} {time}"
        if requested < now:
            conn.rollback()
            return jsonify({
                "status": "error",
                "message": "Cannot book an appointment in the past"
            }), 400

        # Global time slot conflict check
        cursor.execute("""
            SELECT 1 FROM appointment
            WHERE Date = %s AND Time = %s
        """, (date, time))
        if cursor.fetchone():
            conn.rollback()
            return jsonify({
                "status": "error",
                "message": f"Conflict: Another appointment already exists on {date} at {time}"
            }), 409

        # Ensure default owner exists
        cursor.execute("SELECT 1 FROM owner WHERE Owner_id = 1")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO owner (Owner_id, Owner_name, Owner_email, PhoneNUMB)
                VALUES (%s, %s, %s, %s)
            """, (1, "Default Owner", "default@example.com", "0000000000"))

        # Ensure car exists
        cursor.execute("SELECT 1 FROM car WHERE Car_plate = %s", (car_plate,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO car (Car_plate, Model, Year, VIN, Next_Oil_Change, Owner_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                car_plate,
                "UnknownModel",
                2020,
                "VIN000",
                "2025-12-01",
                1
            ))

        # Insert appointment
        cursor.execute("""
            INSERT INTO appointment (Date, Time, Notes, Car_plate)
            VALUES (%s, %s, %s, %s)
        """, (date, time, notes, car_plate))
        appointment_id = cursor.lastrowid

        # Validate and link services
        for service_id in service_ids:
            cursor.execute("SELECT 1 FROM service WHERE Service_ID = %s", (service_id,))
            if cursor.fetchone():
                cursor.execute("""
                    INSERT INTO appointment_service (Appointment_id, Service_ID)
                    VALUES (%s, %s)
                """, (appointment_id, service_id))
            else:
                conn.rollback()
                return jsonify({
                    "status": "error",
                    "message": f"Invalid Service_ID: {service_id}"
                }), 400

        conn.commit()
        return jsonify({
            "status": "success",
            "message": f"Appointment booked for {car_plate} on {date} at {time}"
        }), 201

    except Error as err:
        if conn: conn.rollback()
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    app.run(debug=True)