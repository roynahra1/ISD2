from flask import render_template

def setup_view_appointment_page_route(app):
    @app.route("/viewAppointment/search")
    def view_appointment_page():
        return render_template("viewAppointment.html")