from flask import Blueprint, render_template, request, redirect, session
from services.auth_service import checkLogin, createUser, getUserId

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    username = request.form.get("username")
    password = request.form.get("password")
    success, user_id = checkLogin(username, password)
    if success:
        session["user_id"] = user_id
        session["username"] = username
        return redirect("/")
    return render_template("login.html", loginFailed=True)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmPassword")

    if getUserId(username):
        return render_template("register.html", error="Username already in use.")
    if password != confirmation:
        return render_template("register.html", error="Passwords do not match each other.")
    
    success, newUser = createUser(username, password)
    session["user_id"] = newUser["id"]
    session["username"] = username
    return redirect("/")
