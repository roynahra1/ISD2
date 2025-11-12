from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import database as db
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Database connection and query
        cursor = db.get_db().cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password (assuming you have password hashing)
        if db.verify_password(password, user.get('password_hash', '')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            if request.is_json:
                return jsonify({'message': 'Login successful', 'user': user}), 200
            else:
                return redirect(url_for('appointments'))
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # Field validation
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
            
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
            
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        cursor = db.get_db().cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (username, email))
        if cursor.fetchone():
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Create user
        password_hash = db.hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        db.get_db().commit()
        
        # Get the new user ID
        user_id = cursor.lastrowid
        
        if request.is_json:
            return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
        else:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('appointments'))
            
    except Exception as e:
        db.get_db().rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    if request.method == 'GET':
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return render_template('book.html')
    
    try:
        # Authentication check
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() if request.is_json else request.form
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        car_plate = data.get('car_plate', '').strip()
        date_str = data.get('date', '').strip()
        time_str = data.get('time', '').strip()
        service_ids = data.get('service_ids', [])
        
        # Convert form data if needed
        if isinstance(service_ids, str):
            service_ids = [int(sid) for sid in service_ids.split(',') if sid.isdigit()]
        
        # Field validation
        required_fields = {'car_plate': car_plate, 'date': date_str, 'time': time_str}
        for field, value in required_fields.items():
            if not value:
                return jsonify({'error': f'Field is required: {field}'}), 400
        
        if not service_ids:
            return jsonify({'error': 'At least one service must be selected'}), 400
        
        # Date validation
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if appointment_date < datetime.now().date():
                return jsonify({'error': 'Cannot book appointments in the past'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Time validation
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        
        # Create appointment
        cursor = db.get_db().cursor()
        cursor.execute(
            "INSERT INTO appointments (user_id, car_plate, date, time, status) VALUES (%s, %s, %s, %s, %s)",
            (session['user_id'], car_plate, date_str, time_str, 'booked')
        )
        appointment_id = cursor.lastrowid
        
        # Add services
        for service_id in service_ids:
            cursor.execute(
                "INSERT INTO appointment_services (appointment_id, service_id) VALUES (%s, %s)",
                (appointment_id, service_id)
            )
        
        db.get_db().commit()
        
        if request.is_json:
            return jsonify({'message': 'Appointment booked successfully', 'appointment_id': appointment_id}), 201
        else:
            return redirect(url_for('view_appointments'))
            
    except Exception as e:
        db.get_db().rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/appointments')
def appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('appointments.html')

@app.route('/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment_by_id(appointment_id):
    try:
        cursor = db.get_db().cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, u.username 
            FROM appointments a 
            LEFT JOIN users u ON a.user_id = u.id 
            WHERE a.id = %s
        """, (appointment_id,))
        appointment = cursor.fetchone()
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        return jsonify({'appointment': appointment}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/appointments/select', methods=['POST'])
def select_appointment():
    try:
        # Authentication check
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() if request.is_json else request.form
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        appointment_id = data.get('appointment_id')
        if not appointment_id:
            return jsonify({'error': 'appointment_id is required'}), 400
        
        # Validate appointment exists and belongs to user
        cursor = db.get_db().cursor(dictionary=True)
        cursor.execute("SELECT * FROM appointments WHERE id = %s AND user_id = %s", 
                      (appointment_id, session['user_id']))
        appointment = cursor.fetchone()
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Store selected appointment in session
        session['selected_appointment'] = appointment_id
        
        return jsonify({'message': 'Appointment selected successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/appointments/update', methods=['PUT', 'POST'])
def update_appointment():
    try:
        # Authentication check
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() if request.is_json else request.form
        
        if not data:
            return jsonify({'error': 'No data provided for update'}), 400
        
        # Check if appointment is selected
        appointment_id = session.get('selected_appointment')
        if not appointment_id:
            return jsonify({'error': 'No appointment selected for update'}), 400
        
        # Validate user owns the appointment
        cursor = db.get_db().cursor()
        cursor.execute("SELECT id FROM appointments WHERE id = %s AND user_id = %s", 
                      (appointment_id, session['user_id']))
        if not cursor.fetchone():
            return jsonify({'error': 'Appointment not found or access denied'}), 404
        
        # Build update query dynamically
        updatable_fields = ['car_plate', 'date', 'time', 'status']
        update_data = []
        update_fields = []
        
        for field in updatable_fields:
            if field in data and data[field]:
                update_fields.append(f"{field} = %s")
                update_data.append(data[field].strip())
        
        if not update_fields:
            return jsonify({'error': 'No valid fields provided for update'}), 400
        
        update_data.append(appointment_id)
        
        query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, update_data)
        db.get_db().commit()
        
        return jsonify({'message': 'Appointment updated successfully'}), 200
        
    except Exception as e:
        db.get_db().rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/appointments/delete', methods=['POST', 'DELETE'])
def delete_appointment():
    try:
        # Authentication check
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() if request.is_json else request.form
        appointment_id = data.get('appointment_id') if data else None
        
        if not appointment_id:
            # Try to get from session if not provided directly
            appointment_id = session.get('selected_appointment')
            if not appointment_id:
                return jsonify({'error': 'No appointment specified for deletion'}), 400
        
        # Validate user owns the appointment
        cursor = db.get_db().cursor()
        cursor.execute("SELECT id FROM appointments WHERE id = %s AND user_id = %s", 
                      (appointment_id, session['user_id']))
        if not cursor.fetchone():
            return jsonify({'error': 'Appointment not found or access denied'}), 404
        
        # Delete appointment services first (if foreign key constraints exist)
        cursor.execute("DELETE FROM appointment_services WHERE appointment_id = %s", (appointment_id,))
        
        # Delete appointment
        cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
        db.get_db().commit()
        
        # Clear selected appointment if it was the one deleted
        if session.get('selected_appointment') == appointment_id:
            session.pop('selected_appointment', None)
        
        return jsonify({'message': 'Appointment deleted successfully'}), 200
        
    except Exception as e:
        db.get_db().rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/search', methods=['GET', 'POST'])
def search_appointments():
    if request.method == 'GET':
        return render_template('search.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        if not data:
            return jsonify({'error': 'No search criteria provided'}), 400
        
        car_plate = data.get('car_plate', '').strip()
        if not car_plate:
            return jsonify({'error': 'Car plate is required for search'}), 400
        
        cursor = db.get_db().cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, u.username 
            FROM appointments a 
            LEFT JOIN users u ON a.user_id = u.id 
            WHERE a.car_plate LIKE %s
        """, (f'%{car_plate}%',))
        
        appointments = cursor.fetchall()
        
        return jsonify({'appointments': appointments}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view-appointments')
def view_appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('view_appointments.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)