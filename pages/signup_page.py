from flask import render_template

def setup_signup_page_route(app):
    @app.route("/signup.html")
    def signup_page():
        return render_template("signup.html")