from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from dao.UserDAO import getByEmail, getRoleNameByID
from util.Bcrypt import checkPassword

login_bp = Blueprint("login", __name__)

@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
        else:
            try:
                user = getByEmail(email)
                if user is None or not checkPassword(password, user["password"]):
                    flash("Invalid email or password.", "error")
                else:
                    role_row = getRoleNameByID(user["roleID"])
                    session["user_id"]   = user["userID"]
                    session["username"]  = user["username"]
                    session["role_id"]   = user["roleID"]
                    session["user_role"] = role_row["roleName"] if role_row else ""
                    return redirect(url_for("dashboard.dashboard"))
            except Exception:
                flash("Login failed due to a system error. Please try again.", "error")

    return render_template("login.html")


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login.login"))


@login_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email', '').strip().lower()
    if not email:
        flash('Please provide your email address.', 'error')
        return redirect(url_for('login.login'))

    user = getByEmail(email)
    # For now, do not reveal whether the account exists. In production send an email
    if user:
        # TODO: integrate email sending with password reset token
        flash('If an account exists for that email, a reset link has been sent.', 'info')
    else:
        flash('If an account exists for that email, a reset link has been sent.', 'info')

    return redirect(url_for('login.login'))