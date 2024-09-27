"""
This module contains helper functions for handling operations such as formatting times,
deleting records, and updating records in database tables. It uses SQLAlchemy for 
database interaction and Flask for user feedback through flash messages.
"""

from datetime import datetime, timedelta
from flask import flash
from flask_login import current_user
from flask_mail import Message
from . import scheduler, database
from .models import Reservation, User, Device


def format_time(time):
    """
    Converts a string representation of a date and time to a `datetime` object.
    Args:
        time (str): The string representation of the time in the format "%Y-%m-%dT%H:%M".
    """
    return datetime.strptime(time, "%Y-%m-%dT%H:%M")


def check_if_device_is_available(device_id, start_time, end_time):
    """
    Checks whether a device is available for the given time period by ensuring
    there are no overlapping reservations for that device.
    """
    all_reservations_for_device = Reservation.query.filter_by(device_id=device_id)
    for reservation in all_reservations_for_device:
        # If the new reservation does not overlap with this reservation, continue
        if (reservation.start_time > end_time) or (reservation.end_time < start_time):
            continue
        return False
    return True


def send_reservation_email(email, reservation):
    """
    Sends an email to the user with details about their upcoming reservation.
    """
    msg = Message(subject="Your Reservation is Confirmed!", recipients=[email])

    msg.body = f"""
    Dear {current_user.username},

    Your reservation for {reservation.device_name} has been confirmed.

    Details:
    Device: {reservation.device_name}
    Start Time: {reservation.start_time}
    End Time: {reservation.end_time}
    Reason: {reservation.reason}

    Please be prepared before your reservation begins.

    Best regards,
    The Team
    """

    email.send(msg)


def schedule_reservation_notification(reservation):
    """
    Schedules a job to send an email notification 30 minutes before the reservation start time.
    """
    notification_time = reservation.start_time - timedelta(minutes=30)
    job_id = f"notify_user_{reservation.id}"

    scheduler.add_job(
        func=send_reservation_email,
        trigger="date",
        run_date=notification_time,
        args=[current_user.email_address, reservation],
        id=job_id,
        replace_existing=True,
    )


def check_start_and_end_time(start_time, end_time):
    """
    Verifies that start and end time fit criteria
    """
    time_now = datetime.now()
    if start_time < time_now or end_time < time_now:
        flash("You cannot schedule a reservation in the past.", category="error")
        return False

    if start_time >= end_time:
        flash("Start time must be before end time.", category="error")
        return False
    return True


def check_if_user_exists_from_username(username):
    """
    Checks if the user exists throught their username
    """
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    return False


def check_if_device_exists_from_device_id(device_id):
    """
    Checks if the device exists throught their device id
    """
    device = Device.query.get(device_id)
    if device:
        return True
    return False


def check_availability_of_device_name(device_name, start_time, end_time):
    """
    Checks the availability of all devices by their device name
    """
    all_devices = Device.query.filter_by(device_name=device_name).all()

    if not all_devices:
        flash(f"No devices found with the name {device_name}.", category="error")
        return False

    for device in all_devices:
        if check_if_device_is_available(device.id, start_time, end_time):
            return device.id

    flash(
        "No devices are available with the specified name.",
        category="error",
    )
    return False


def table_update_item(success_message, error_message):
    """
    Updates an item from the table and performs exception handling
    """
    try:
        database.session.commit()
        flash(success_message, category="success")
        return True
    except Exception as e:
        database.session.rollback()
        flash(f"{error_message}  {str(e)}", category="error")
        return False


def table_create_item(item, success_message, error_message):
    """
    Create an item in the table and performs exception handling
    """
    try:
        database.session.add(item)
        database.session.commit()
        flash(success_message, category="success")
        return True
    except Exception as e:
        database.session.rollback()
        flash(f"{error_message}  {str(e)}", category="error")
        return False


def table_delete_item(item, success_message, error_message):
    """
    Deletes an item from the table and performs exception handling
    """
    try:
        database.session.delete(item)
        database.session.commit()
        flash(success_message, category="success")
        return True
    except Exception as e:
        database.session.rollback()
        flash(f"{error_message}  {str(e)}", category="error")
        return False
