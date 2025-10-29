from flask import Flask, request, jsonify, render_template
import hashlib
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'isd'
}

def sha1_hash(password):
    return hashlib.sha1(password.encode()).hexdigest()

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    hashed_input = sha1_hash(password)

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT Password FROM admin WHERE Username = %s", (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        # 🔍 Debug output
        print(f"Username entered: {username}")
        print(f"Password entered: {password}")
        print(f"Hashed input: {hashed_input}")
        print(f"Stored hash: {result[0] if result else 'No user found'}")

        if result and result[0].strip() == hashed_input:
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'message': 'Invalid username or password'}), 401

    except Exception as err:
        return jsonify({'message': f'Database error: {err}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)