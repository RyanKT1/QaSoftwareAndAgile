"""
This module handles the routes related to device management, including CRUD operations
(create, read, update, and delete) for devices in the system.
"""

from datetime import datetime
from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Device, Reservation
from .helper_functions import (
    format_time,
    table_create_item,
    table_delete_item,
    table_update_item,
)

device_blueprint = Blueprint("device", __name__)


@device_blueprint.route("/", methods=["GET", "POST"])
@login_required
def home():
    """
    Handles the default page for device management
    GET: Queries the database to fetch all device entries and renders the `read_device.html` page
         to display the devices.
    POST: If sent with the 'DELETE' method then it will check if the device exists and then render
          a confirm delete page if there are any reservations tied to that device.


    """
    if request.method == "GET":
        all_devices = Device.query.all()
        return render_template(
            "read_device.html", user=current_user, devices=all_devices
        )
    if (
        request.method == "POST"
        and request.form.get("_method") == "DELETE"
        and current_user.administrator
    ):
        device_id = request.form.get("device_id")
        device = Device.query.get(device_id)

        if not device:
            flash("Device not found.", category="error")
            return redirect(url_for("device.home"))
        reservations = Reservation.query.filter_by(device_id=device_id).all()
        if reservations:
            return render_template(
                "confirm_device_delete.html",
                device=device,
                user=current_user,
                reservations=reservations,
            )

        return redirect(url_for("device.home"))
    return redirect(url_for("views.home"))


@device_blueprint.route("/confirm_delete", methods=["POST"])
@login_required
def confirm_delete():
    """
    Confirms that the administrator user wants to delete the device.
    POST: Deletes the chosen device if the device is found
          and the administrator user has confirmed 'yes'.
    """
    device_id = request.form.get("device_id")
    device = Device.query.get(device_id)
    confirm = request.form.get("confirm")

    if not device:
        flash("Device not found.", category="error")
        return redirect(url_for("device.home"))

    if confirm == "yes" and current_user.administrator:
        # Admin confirmed, delete device
        success_message = f"Device {device.device_name} has been deleted successfully."
        error_message = f"Error deleting Device {device.device_name}:"
        table_delete_item(device, success_message, error_message)

    elif not current_user.administrator:
        flash("You are not administrator", category="error")
    else:
        flash(f"Deletion of device {device.device_name} was canceled.", category="info")

    return redirect(url_for("device.home"))


@device_blueprint.route("/see_availability", methods=["GET", "POST"])
@login_required
def see_availability():
    """
    Displays a devices availability.
    POST: Loops throught all reservations assigned to a specific device id and
          appends the availabilty between the end time of a reservation and
          the next reservations start time.
    """
    device_id = request.args.get("device_id")
    if not device_id:
        flash("Device ID not provided.", category="error")
        return redirect(url_for("device.home"))

    device = Device.query.get(device_id)

    if not device:
        flash("Device not found.", category="error")
        return redirect(url_for("device.home"))
    now = datetime.now()
    reservations = (
        Reservation.query.filter_by(device_id=device_id)
        .filter(Reservation.start_time > now)
        .order_by(Reservation.start_time)
        .all()
    )

    availability_slots = []

    # Start of the availability: Before the first reservation
    if reservations:
        if now < reservations[0].start_time:
            availability_slots.append({"start": now, "end": reservations[0].start_time})
            # Check gaps between reservations
        for i in range(len(reservations) - 1):
            end_of_current_reservation = reservations[i].end_time
            start_of_next_reservation = reservations[i + 1].start_time

            if end_of_current_reservation < start_of_next_reservation:
                availability_slots.append(
                    {
                        "start": end_of_current_reservation,
                        "end": start_of_next_reservation,
                    }
                )

        availability_slots.append(
            {
                "start": reservations[-1].end_time,
                "end": None,  # Available indefinitely after the last reservation
            }
        )
    else:
        # If no reservations, the device is fully available from now
        availability_slots.append(
            {"start": now, "end": None}  # No end time, fully available
        )

    return render_template(
        "see_device_availability.html",
        user=current_user,
        reservations=reservations,
        availability_slots=availability_slots,
        device=device,
    )


@device_blueprint.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """
    Updates device information based on user input.

    POST: Allows an administrator to update device details by specifying which field to update.
    """
    device_id = request.args.get("device_id")
    if not device_id:
        flash("Device ID not provided.", category="error")
        return redirect(url_for("device.home"))

    device = Device.query.get(device_id)

    if not device:
        flash("Device not found.", category="error")
        return redirect(url_for("device.home"))

    if request.method == "POST" and current_user.administrator:
        device_fields = (
            "device_name",
            "device_brand",
            "device_status",
            "device_type",
            "last_use",
        )
        for device_field in device_fields:
            value = request.form.get(device_field)
            if device_field == "last_use" and value:
                value = format_time(value)
                if value > datetime.now():
                    flash(
                        "The last use of a device can not be in the future",
                        category="info",
                    )
                    value = None

            if device_field == "device_name" and value:
                all_current_device_reservations = Reservation.query.filter_by(
                    device_id=device_id
                ).all()
                for reservation in all_current_device_reservations:
                    reservation.device_name = value
                    setattr(device, device_field, value)
        success_message = f"Device {device.device_name} updated successfully!"
        error_message = "Error updating device:"
        if table_update_item(success_message, error_message):
            return redirect(url_for("device.home"))
        return redirect(url_for("device.update", device_id=device.id))

    if not current_user.administrator:
        flash("You are not administrator", category="error")
        return redirect(url_for("device.home"))
    return render_template("update_device.html", device=device, user=current_user)


@device_blueprint.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Creates a new device and adds it to the system.

    POST: Allows an administrator to create a new device by providing details such as
          the device name, brand, status, and type. The new device is saved to the database.
    """
    if request.method == "POST" and current_user.administrator:
        device_name = request.form.get("device_name")
        device_brand = request.form.get("device_brand")
        device_status = request.form.get("device_status")
        device_type = request.form.get("device_type")

        new_device = Device(
            id=None,
            device_brand=device_brand,
            device_name=device_name,
            device_status=device_status,
            device_type=device_type,
        )
        success_message = f"Device {device_name} created successfully!"
        error_message = "Error creating device:"
        if table_create_item(new_device, success_message, error_message):
            return redirect(url_for("device.home"))
        return redirect(url_for("device.create"))
    if not current_user.administrator:
        flash("You are not administrator", category="error")
        return redirect(url_for("device.home"))

    return render_template("create_device.html", user=current_user)
