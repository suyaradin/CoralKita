import re
from flask import Blueprint, flash, redirect, render_template, request, url_for
from dao.UserDAO import createUser, getByEmail, getRoleByName
from util.Bcrypt import hashPassword

register_bp = Blueprint("register", __name__)

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username  = request.form.get("name", "").strip()
        email     = request.form.get("email", "").strip().lower()
        password  = request.form.get("password", "")
        role_name = request.form.get("role-selection", "").strip()

        if not username:
            flash("Full name is required.", "error")
        elif not email or "@" not in email:
            flash("A valid email address is required.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif not re.search(r'[a-zA-Z]', password):
            flash("Password must contain at least 1 letter.", "error")
        elif not re.search(r'\d', password):
            flash("Password must contain at least 1 number.", "error")
        elif getByEmail(email):
            flash("This email is already registered.", "error")
        else:
            try:
                role_id = getRoleByName(role_name)
                if role_id is None:
                    flash("Selected role does not exist in Role table.", "error")
                else:
                    password_hash = hashPassword(password)
                    createUser(username, email, password_hash, role_id)
                    flash("Account created successfully. Please login.", "success")
                    return redirect(url_for("login.login"))
            except Exception:
                flash("Registration failed due to a system error. Please try again.", "error")

    return render_template("register.html")