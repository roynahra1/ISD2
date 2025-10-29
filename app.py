from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import cv2
import numpy as np
import pytesseract
import re
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Tesseract path
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# MySQL config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'isd'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ---------- ROUTES ----------

@app.route('/')
def home():
    return "✅ Flask server is running"

@app.route('/appointment.html')
def serve_appointment_form():
    return render_template('appointment.html')

@app.route('/add-car')
def add_car_page():
    return render_template('add_car.html')

@app.route('/detect', methods=['POST'])
def detect_plate():
    try:
        file = request.files['image']
        image_bytes = file.read()
        img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"success": False, "message": "Failed to decode image"})

        plate_number, confidence = detect_license_plate(img)

        if plate_number:
            car_info = fetch_car_info(plate_number)
            return jsonify({
                "success": True,
                "plate_number": plate_number,
                "confidence": confidence,
                "car_info": car_info if car_info else "No record found"
            })

        return jsonify({"success": False, "message": "No valid plate detected"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/car-info', methods=['POST'])
def get_car_info():
    try:
        data = request.get_json()
        plate_number = data.get('plate_number')

        if not plate_number:
            return jsonify({"success": False, "message": "Plate number is required"})

        car_info = fetch_car_info(plate_number)
        return jsonify({
            "success": True,
            "car_info": car_info if car_info else None
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})



@app.route('/update-car', methods=['POST'])
def update_car_info():
    try:
        data = request.get_json()
        plate = data['plate_number']
        kms = data['kms']
        notes = data['notes']
        today = datetime.now().date()
        next_due = today + timedelta(days=90)

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE car_maintenance
            SET last_oil_change = %s,
                next_oil_change_due = %s,
                kms = %s,
                notes = %s
            WHERE plate_number = %s
        ''', (today, next_due, kms, notes, plate))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Car info updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ---------- UTILS ----------

def detect_license_plate(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            if 2 <= aspect_ratio <= 5 and w > 50 and h > 20:
                roi = gray[y:y+h, x:x+w]
                roi = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                roi = cv2.medianBlur(roi, 3)
                text = pytesseract.image_to_string(roi, config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                cleaned = clean_plate_text(text)
                if is_valid_plate(cleaned):
                    return cleaned, min(0.7 + len(cleaned) * 0.05, 0.95)

    text = pytesseract.image_to_string(gray, config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    cleaned = clean_plate_text(text)
    if is_valid_plate(cleaned):
        return cleaned, min(0.6 + len(cleaned) * 0.05, 0.9)

    return None, 0.0

def clean_plate_text(text):
    return re.sub(r'[^A-Z0-9]', '', text.upper())

def is_valid_plate(text):
    return len(text) >= 4 and len(text) <= 8 and any(c.isalpha() for c in text) and any(c.isdigit() for c in text)

def fetch_car_info(plate_number):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT owner_name, model, kms, last_oil_change, next_oil_change_due, notes
            FROM car_maintenance
            WHERE plate_number = %s
        ''', (plate_number,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            return {
                "owner_name": result[0],
                "model": result[1],
                "kms": result[2],
                "last_oil_change": str(result[3]),
                "next_oil_change_due": str(result[4]),
                "notes": result[5]
            }
    except mysql.connector.Error as err:
        print("MySQL Error:", err)

    return None

# ---------- RUN ----------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)