"""
This module manages reservation-related operations, such as creating, reading,
updating, and deleting reservations.
"""

from datetime import datetime
from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Reservation, Device
from .helper_functions import (
    format_time,
    schedule_reservation_notification,
    check_if_device_is_available,
    check_start_and_end_time,
    check_if_user_exists_from_username,
    check_if_device_exists_from_device_id,
    check_availability_of_device_name,
    table_create_item,
    table_update_item,
    table_delete_item,
)

reservation_blueprint = Blueprint("reservation", __name__)


@reservation_blueprint.route("/", methods=["GET", "POST"])
@login_required
def home():
    """
    Handles the default page for reservation management.
    GET: Queries the database to fetch all reservations entries and
         renders the `read_reservation.html` page to display the reservation.
    POST: If sent with the 'DELETE' method then it will check if the reservation exists and then
          deletes the reservation if the user is administrator or if it was their own reservation.

    """
    if request.method == "GET":
        # Checks whether user requests to see all devices or just their own (only for administrator user)
        show_all = request.args.get("show_all", default="false").lower() == "true"
        if current_user.administrator and show_all:
            reservations = Reservation.query.all()
            flash("Displaying all users' reservations", category="info")
        else:
            reservations = Reservation.query.filter_by(
                username=current_user.username
            ).all()
            if current_user.administrator:
                flash(
                    "Displaying only your reservations. Toggle to see all reservations.",
                    category="info",
                )
        return render_template(
            "read_reservation.html",
            user=current_user,
            reservations=reservations,
            show_all=show_all,
        )
    if request.method == "POST" and request.form.get("_method") == "DELETE":
        reservation_id = request.form.get("reservation_id")
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            flash("Reservation not found.", category="error")
            return redirect(url_for("reservation.home"))

        # Allow only admin or the owner of the reservation to delete
        if current_user.administrator or reservation.username == current_user.username:
            success_message = "Reservation deleted successfully!"
            error_message = "Error deleting Reservation:"
            table_delete_item(reservation, success_message, error_message)
        else:
            flash(
                "You do not have permission to delete this reservation.",
                category="error",
            )

    return redirect(url_for("views.home"))


@reservation_blueprint.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Allows the user to create a new reservation.

    GET: Toggles the `using_device_id` variable which lets the user choose whether to
         scheldue a reservation using the device id or the device name.
    POST: Collects reservation details from the form, checks device availability, and
          creates a new reservation if the device is available.
    """
    if request.method == "GET":
        using_device_id = request.args.get("using_device_id")
        if using_device_id == "True":
            using_device_id = "False"
        else:
            using_device_id = "True"
        return render_template(
            "create_reservation.html",
            user=current_user,
            using_device_id=using_device_id,
        )
    if request.method == "POST":
        device_name = request.form.get("device_name")
        device_id = request.form.get("device_id")
        start_time = format_time(request.form.get("start_time"))
        end_time = format_time(request.form.get("end_time"))
        reason = request.form.get("reason")

        if not check_start_and_end_time(start_time, end_time):
            return redirect(url_for("reservation.create"))

        # Device availability validation
        if device_id:
            if not check_if_device_is_available(device_id, start_time, end_time):
                flash(
                    "The selected device is not available at this time.",
                    category="error",
                )
                return redirect(url_for("reservation.create"))
            device = Device.query.filter_by(id=device_id).first()
            if not device:
                flash("Device not found.", category="error")
                return redirect(url_for("reservation.home"))
            device_name = device.device_name

        else:
            # Look for devices matching device_name and check availability
            device_id = check_availability_of_device_name(
                device_name, start_time, end_time
            )
            if not device_id:
                return redirect(url_for("reservation.create"))

            if not check_if_user_exists_from_username(current_user.username):
                flash("Username not does exist", category="error")
                return redirect(url_for("reservation.create"))

        device = Device.query.filter_by(id=device_id).first()
        new_reservation = Reservation(
            device_id=device_id,
            device_name=device.device_name,
            username=current_user.username,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
        )
        schedule_reservation_notification(new_reservation)
        success_message = "Reservation created successfully!"
        error_message = "Error creating reservation:"
        if table_create_item(new_reservation, success_message, error_message):
            return redirect(url_for("reservation.home"))
        return redirect(url_for("reservation.create"))
    return render_template("create_reservation.html", user=current_user)


@reservation_blueprint.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """
    Updates an existing reservation based on user input.

    POST: Allows a user to update the details of a reservation, such as
          the device ID, device name, reservation times, or reason.
    """
   
    reservation_id = request.args.get("reservation_id")
    if not reservation_id:
        flash("Reservation ID not provided.", category="error")
        return redirect(url_for("reservation.home"))
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        flash("Reservation not found.", category="error")
        return redirect(url_for("reservation.home"))

    if request.method == "POST" and current_user.administrator:
        device_id = request.form.get("device_id")
        device_name = request.form.get("device_name")
        username = request.form.get("username")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        reason = request.form.get("reason")
        if reason:
            reservation.reason = reason
        if username:
            if not check_if_user_exists_from_username(username):
                flash("Username does not exist", category="error")
                return url_for("reservation.update", reservation=reservation)
            reservation.username = username
        if start_time and end_time:
            start_time = format_time(start_time)
            end_time = format_time(end_time)
            if not check_start_and_end_time(start_time, end_time):
                return url_for("reservation.update", reservation=reservation)
            reservation.start_time = start_time
            reservation.end_time = end_time
        elif start_time:
            start_time = format_time(start_time)
            if not check_start_and_end_time(start_time, reservation.end_time):
                return url_for("reservation.update", reservation=reservation)
            reservation.start_time = start_time
        elif end_time:
            end_time = format_time(end_time)
            if not check_start_and_end_time(reservation.start_time, end_time):
                return url_for("reservation.update", reservation=reservation)
            reservation.end_time = end_time
        start_time = start_time if start_time else reservation.start_time
        end_time = end_time if end_time else reservation.end_time
        if device_name:
            device_id = check_availability_of_device_name(
                device_name, start_time, end_time
            )
            if not device_id:
                return url_for("reservation.update", reservation=reservation)
            reservation.device_name = device_name
        if device_id:
            if not check_if_device_exists_from_device_id(device_id):
                flash("Device does not exist", category="error")
                return url_for("reservation.update", reservation=reservation)
            if check_if_device_is_available(device_id, start_time, end_time):
                reservation.device_id = device_id
            else:
                flash("Device is not available for this time", category="error")
                return url_for("reservation.update", reservation=reservation)
        success_message = "Reservation updated successfully!"
        error_message = "Error updating reservation:"
        if table_update_item(success_message, error_message):
            return redirect(url_for("reservation.home"))
        return redirect(url_for("reservation.update", reservation=reservation))
    return render_template(
        "update_reservation.html", reservation=reservation, user=current_user
    )
