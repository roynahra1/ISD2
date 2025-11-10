import os
from flask import Flask
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = os.getenv("APP_SECRET_KEY", os.urandom(24))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax", 
    SESSION_COOKIE_SECURE=False
)

def make_app():
    """Setup and return the Flask application with ALL routes"""
    
    # Import and setup all auth routes
    from auth.login import setup_login_route
    from auth.signup import setup_signup_route
    from auth.logout import setup_logout_route
    from auth.status import setup_status_route
    
    # Import and setup all appointment routes
    from appointments.add import setup_add_appointment_route
    from appointments.update import setup_update_appointment_route
    from appointments.delete import setup_delete_appointment_route
    from appointments.search import setup_search_appointment_route
    from appointments.select import setup_select_appointment_route
    from appointments.get_by_id import setup_get_by_id_route
    from appointments.get_current import setup_get_current_route
    
    # Import and setup all page routes
    from pages.login_page import setup_login_page_route
    from pages.appointment_page import setup_appointment_page_route
    from pages.view_appointment_page import setup_view_appointment_page_route
    from pages.update_appointment_page import setup_update_appointment_page_route
    from pages.signup_page import setup_signup_page_route

    # Setup ALL routes
    setup_login_route(app)
    setup_signup_route(app)
    setup_logout_route(app)
    setup_status_route(app)
    
    setup_add_appointment_route(app)
    setup_update_appointment_route(app)
    setup_delete_appointment_route(app)
    setup_search_appointment_route(app)
    setup_select_appointment_route(app)
    setup_get_by_id_route(app)
    setup_get_current_route(app)
    
    setup_login_page_route(app)
    setup_appointment_page_route(app)
    setup_view_appointment_page_route(app)
    setup_update_appointment_page_route(app)
    setup_signup_page_route(app)
    
    return app

# ✅ CRITICAL: This line must be present and call make_app()
app = make_app()

if __name__ == "__main__":
    print("Server running on http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)