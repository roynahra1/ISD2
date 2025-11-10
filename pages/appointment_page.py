from flask import render_template

def setup_appointment_page_route(app):
    @app.route("/appointment.html")
    def appointment_page():
        return render_template("appointment.html")