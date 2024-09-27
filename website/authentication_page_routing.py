"""
This module handles the authentication-related routes for the Flask web application.
"""

import re
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .helper_functions import check_if_user_exists_from_username, table_create_item
from .models import User

authentication_blueprint = Blueprint("authentication", __name__)


@authentication_blueprint.route("/login", methods=["GET", "POST"])
def login_page():
    """
    Handles user login by validating username, password, and security pin.

    GET: Renders the login page.
    POST: Checks if the provided username exists, and if the password and security pin are correct.
          If authenticated, logs the user in and redirects to the home page.
          If credentials are incorrect, flashes an error message.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        security_pin = request.form.get("pin")
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password) and check_password_hash(
                user.security_pin, security_pin
            ):
                flash("Logged in successfully", category="success")
                login_user(user, remember=True)
                return redirect(url_for("views.home"))
            flash("Incorrect credentials, try again", category="error")
        else:
            flash("Please enter a valid username", category="error")
    return render_template("login.html", text="Testing login page", user=current_user)


@authentication_blueprint.route("/logout")
@login_required
def logout_page():
    """
    Logs out the current user and redirects to the login page.
    """
    logout_user()
    return redirect(url_for("authentication.login_page"))


@authentication_blueprint.route("/signup", methods=["GET", "POST"])
def signup_page():
    """
    Handles user registration by validating user input and creating a new user.

    GET: Renders the signup page.
    POST: Validates the provided email, username, password, and security pin. If validation
          passes and the username is not already taken, creates a new user, logs them in,
          and redirects to the home page.
          If any validation fails, flashes an appropriate error message.
    """
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        security_pin = request.form.get("pin")

        if check_if_user_exists_from_username(username):
            flash("Username already exists", category="error")
        else:
            if len(password) < 7:
                flash("Password must be greater than 7 characters", category="error")
            elif not re.search(r"[^@]+@[^@]+\.[^@]+", email):
                flash("Enter a valid email", category="error")
            elif len(username) < 1:
                flash("Username must contain at least 1 character", category="error")
            elif int(security_pin) < 9999999:
                flash("Security pin must contain at least 8 digits", category="error")
            else:
                new_user = User(
                    email_address=email,
                    username=username,
                    password=generate_password_hash(password, method="pbkdf2:sha256"),
                    security_pin=generate_password_hash(
                        security_pin, method="pbkdf2:sha256"
                    ),
                    administrator=True,
                )
                success_message = "Account created!"
                error_message = "Error creating account:"
                if table_create_item(new_user, success_message, error_message):
                    login_user(new_user, remember=True)
                    return redirect(url_for("views.home"))
                return redirect(url_for("authentication.signup_page"))
    return render_template("sign_up.html", user=current_user)
