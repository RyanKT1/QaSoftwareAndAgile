"""
This modules handles user management including the user settings , delete and update account and
read operations on all users.
"""

import re
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user, login_user
from werkzeug.security import check_password_hash, generate_password_hash
from .helper_functions import (
    check_if_user_exists_from_username,
    table_delete_item,
    table_update_item,
)
from .models import User, Reservation


user_blueprint = Blueprint("user", __name__)


@user_blueprint.route("/", methods=["GET", "POST"])
@login_required
def user_settings():
    """
    Displays and handles updates to user settings (username, email, password, and security pin).
    Requires re-authentication before making changes.
    """
    auth_timeout = 15  # in minutes
    last_auth_time = session.get("last_auth_time")
    if (
        not last_auth_time
        or (datetime.now() - datetime.fromtimestamp(last_auth_time)).total_seconds()
        > auth_timeout * 60
    ):
        flash("Please re-authenticate to change your settings.", category="warning")
        return redirect(url_for("user.reauthenticate"))

    return render_template("user_settings.html", user=current_user)


@user_blueprint.route("/update", methods=["GET", "POST"])
@login_required
def change_details():
    """
    Updates the details of the user based on their input.

    POST: Allows a user to update the details of their own user, such as
          the password, security pin, email, or username.
    """
    auth_timeout = 15  # in minutes
    last_auth_time = session.get("last_auth_time")
    if (
        not last_auth_time
        or (datetime.now() - datetime.fromtimestamp(last_auth_time)).total_seconds()
        > auth_timeout * 60
    ):
        flash("Please re-authenticate to change your settings.", category="warning")
        return redirect(url_for("user.reauthenticate"))
    if request.method == "POST":
        # Update password

        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if new_password:
            if len(new_password) < 7:
                flash("Password must be at least 7 characters long.", category="error")
                return redirect(url_for("user.user_settings"))

            if new_password != confirm_password:
                flash("New password and confirmation do not match.", category="error")
                return redirect(url_for("user.user_settings"))
            current_user.password = generate_password_hash(
                new_password, method="pbkdf2:sha256"
            )

        # Update username
        new_username = request.form.get("username")

        if new_username and new_username != current_user.username:
            if len(new_username) < 3:
                flash("Username must be at least 3 characters long.", category="error")
                return redirect(url_for("user.user_settings"))
            # Check if the username already exists
            if check_if_user_exists_from_username(new_username):
                flash(
                    "Username already taken. Please choose another.", category="error"
                )
                return redirect(url_for("user.user_settings"))
            all_current_user_reservations = Reservation.query.filter_by(
                username=current_user.username
            ).all()
            for reservation in all_current_user_reservations:
                reservation.username = new_username
            current_user.username = new_username

        # Update email

        new_email = request.form.get("email")
        if new_email and new_email != current_user.email_address:
            if not re.search(r"[^@]+@[^@]+\.[^@]+", new_email):
                flash("Enter a valid email.", category="error")
                return redirect(url_for("user.user_settings"))
            current_user.email_address = new_email

        # Update security pin
        new_security_pin = request.form.get("security_pin")
        confirm_security_pin = request.form.get("confirm_security_pin")
        if new_security_pin:
            if len(new_security_pin) < 8 or not new_security_pin.isdigit():
                flash("Security pin must be at least 8 digits.", category="error")
                return redirect(url_for("user.user_settings"))

            if new_security_pin != confirm_security_pin:
                flash("Security pin and confirmation do not match.", category="error")
                return redirect(url_for("user.user_settings"))

            # Hash the new security pin and update
            current_user.security_pin = generate_password_hash(
                new_security_pin, method="pbkdf2:sha256"
            )
        success_message = "Your details have been updated successfully!"
        error_message = "Error updating user:"
        if table_update_item(success_message, error_message):
            login_user(current_user, remember=True)
            return redirect(url_for("views.home"))
        return redirect(url_for("user.user_settings"))

    return render_template("user_settings_update.html", user=current_user)


@user_blueprint.route("/reauthenticate", methods=["GET", "POST"])
@login_required
def reauthenticate():
    """
    Forces the user to Re-Authenticate.
    All user settings functions check if the user has reauthenticated in the last 15 minutes,
    if they have not then they are brought to this function.
    POST: Checks the password and security pin that the user has entered with the current password and
          security pin and if they match then the user last authentication time is updated.
    """
    if request.method == "POST":
        # Get current password for re-authentication
        password = request.form.get("password")
        pin = request.form.get("pin")
        # Re-authentication check
        if not check_password_hash(current_user.password, password):
            flash("Incorrect credentials. Please try again.", category="error")
            return redirect(url_for("user.reauthenticate"))

        if not check_password_hash(current_user.security_pin, pin):
            flash(
                "Incorrect credentials. Please try again.", category="error"
            )
            return redirect(url_for("user.reauthenticate"))
        session["last_auth_time"] = datetime.now().timestamp()
        return redirect(url_for("user.user_settings"))

    return render_template("user_settings_reauthenticate.html", user=current_user)


@user_blueprint.route("/delete", methods=["POST"])
@login_required
def delete_account():
    """
    Deletes the account of the current user.
    POST: Checks if the current 'user_id' exists and if it does then deletes that account and
          redirects the user to the login/signup page.

    """
    auth_timeout = 15  # in minutes
    last_auth_time = session.get("last_auth_time")
    if not current_user.administrator:
        flash("You are not administrator", category="error")
        redirect(url_for("views.home"))
    if (
        not last_auth_time
        or (datetime.now() - datetime.fromtimestamp(last_auth_time)).total_seconds()
        > auth_timeout * 60
    ):
        flash("Please re-authenticate to change your settings.", category="warning")
        return redirect(url_for("user.reauthenticate"))
    if request.method == "POST" and request.form.get("_method") == "DELETE":
        user_id = current_user.id

        user = User.query.filter_by(id=user_id).one()
        username = user.username
        # Ensures that user exists in table
        if not user:
            flash("User does not exist in system", category="error")
            return redirect(url_for("user.user_settings"))
        success_message = f"User {username} successfully deleted!"
        error_message = "Error deleting account:"
        if table_delete_item(user, success_message, error_message):
            return redirect(url_for("auth.logout_page"))
    return redirect(url_for("views.home"))


@user_blueprint.route("/admin", methods=["GET", "POST"])
@login_required
def admin_view():
    """
    Handles the request for the administrator view page.
    GET: Queries the database to fetch all user entries and renders the `read_user.html` page
         to display the users.
    POST: If the chosen user exists in the database  and the current user is administrator then
          promote the chosen user to administrator.
    """

    if request.method == "GET" and current_user.administrator:
        all_users = User.query.all()
        return render_template("read_user.html", user=current_user, users=all_users)
    if not current_user.administrator:
        flash("You are not administrator", category="error")
        redirect(url_for("views.home"))
    if request.method == "POST" and current_user.administrator:
        user_id = request.form.get("user_id")
        user = User.query.filter_by(id=user_id)
        # Ensures that user exists in table
        if not user:
            flash("User does not exist in system", category="error")
            return redirect(url_for("user.user_settings"))
        user.administrator = True
        success_message = "User successfully promoted to administrator!"
        error_message = "Error making user administrator:"
        table_update_item(success_message, error_message)
        return redirect(url_for("user.admin_view"))
    return redirect(url_for("user.user_settings"))
