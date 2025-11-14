from flask import render_template

def setup_login_page_route(app):
    @app.route("/login.html")
    def login_page():
        return render_template("login.html")