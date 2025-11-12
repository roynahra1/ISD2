import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

def get_db():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'car_service'),
            autocommit=False
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        raise

def hash_password(password):
    """Hash a password for storing"""
    return generate_password_hash(password)

def verify_password(password, password_hash):
    """Verify a stored password against one provided by user"""
    if not password_hash:
        return False
    return check_password_hash(password_hash, password)

def serialize_datetime(obj):
    """Serialize datetime objects for JSON response"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def safe_close(conn):
    """Safely close database connection"""
    try:
        if conn and conn.is_connected():
            conn.close()
    except Exception as e:
        print(f"Error closing connection: {e}")

def init_db():
    """Initialize database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create appointments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                car_plate VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                status ENUM('booked', 'completed', 'cancelled') DEFAULT 'booked',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create services table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10,2),
                duration_minutes INT
            )
        """)
        
        # Create appointment_services junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointment_services (
                appointment_id INT,
                service_id INT,
                PRIMARY KEY (appointment_id, service_id),
                FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
            )
        """)
        
        # Insert sample services
        cursor.execute("""
            INSERT IGNORE INTO services (id, name, description, price, duration_minutes) VALUES
            (1, 'Oil Change', 'Standard oil and filter change', 49.99, 30),
            (2, 'Tire Rotation', 'Rotate all four tires', 29.99, 45),
            (3, 'Brake Inspection', 'Complete brake system inspection', 39.99, 60),
            (4, 'Engine Diagnostic', 'Computerized engine diagnostic', 79.99, 90)
        """)
        
        conn.commit()
        print("Database initialized successfully")
        
    except mysql.connector.Error as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        safe_close(conn)

# Initialize database when module is imported
if __name__ != '__main__':
    try:
        init_db()
    except:
        pass  # Database might not be available during tests