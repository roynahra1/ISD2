from flask import render_template, redirect, session

def setup_update_appointment_page_route(app):
    @app.route("/updateAppointment.html")
    def update_appointment_page():
        if not session.get("logged_in"):
            return redirect("/login.html")
        if not session.get("selected_appointment"):
            return redirect("/viewAppointment/search")
        return render_template("updateAppointment.html")