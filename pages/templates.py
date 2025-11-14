from flask import render_template, redirect, session

def setup_template_pages(app):
    @app.route("/login.html")
    def login_page():
        return render_template("login.html")

    @app.route("/appointment.html")
    def appointment_page():
        return render_template("appointment.html")

    @app.route("/viewAppointment/search")
    def view_appointment_page():
        return render_template("viewAppointment.html")

    @app.route("/updateAppointment.html")
    def update_appointment_page():
        if not session.get("logged_in"):
            return redirect("/login.html")
        if not session.get("selected_appointment"):
            return redirect("/viewAppointment/search")
        return render_template("updateAppointment.html")

    @app.route("/signup.html")
    def signup_page():
        return render_template("signup.html")