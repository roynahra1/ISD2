<<<<<<< HEAD
from app import create_app

if __name__ == "__main__":
    app = create_app()
    print("🚀 Development server starting on http://localhost:5000")
    print("📁 Debug mode: ON")
    app.run(debug=True, host='0.0.0.0', port=5000)
=======
from app import make_app

if __name__ == "__main__":
    app = make_app()
    print("Starting ISD Appointment System...")
    app.run(debug=True, host="0.0.0.0", port=5000)
>>>>>>> 8a7626db99416992d066a2ebfc1b43e7caff1293
