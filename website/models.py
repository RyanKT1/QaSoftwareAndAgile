"""
This module defines the database models for the Flask web application. These models represent
the User, Device, and Reservation entities in the system, and are used to handle CRUD operations 
and relationships in the database using SQLAlchemy.
"""

from flask_login import UserMixin
from . import database as db

class User(db.Model, UserMixin):
    """
    Represents a user in the system, with details required for authentication and authorization.

    Attributes:
        id (int): The primary key for the user (auto-incremented).
        username (str): The username of the user, must be unique.
        email_address (str): The email address associated with the user.
        password (str): The hashed password for the user's account.
        security_pin (int): A hashed security pin used for additional authentication.
        administrator (bool): A flag indicating if the user has admin privileges.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True)
    email_address = db.Column(db.String(150))
    password = db.Column(db.String(150))
    security_pin = db.Column(db.Integer)
    administrator = db.Column(db.Boolean)


class Device(db.Model):
    """
    Represents a device in the system, which can be reserved by users.

    Attributes:
        id (int): The primary key for the device (auto-incremented).
        device_brand (str): The brand of the device (e.g., Apple, Samsung).
        device_name (str): The name or model of the device (e.g., iPhone 12).
        device_status (str): The current status of the device (e.g., Active, inactive, maintenance).
        device_type (str): The type of the device (e.g., Laptop, Phone).
        last_use (datetime): The last recorded use of the device.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_brand = db.Column(db.String(150))
    device_name = db.Column(db.String(150))
    device_status = db.Column(db.String(150))
    device_type = db.Column(db.String(150))
    last_use = db.Column(db.DateTime(timezone=True))


class Reservation(db.Model):
    """
    Represents a reservation of a device by a user.

    Attributes:
        id (int): The primary key for the reservation (auto-incremented).
        device_id (int): The ID of the reserved device, references the Device model.
        device_name (str): The name of the reserved device, references the Device model.
        username (str): The username of the user who made the reservation, references the User model.
        start_time (datetime): The start time of the reservation.
        end_time (datetime): The end time of the reservation.
        reason (str): A business reason provided by the user for the reservation.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey("device.id"))
    device_name = db.Column(db.String(150), db.ForeignKey("device.device_name"))
    username = db.Column(db.String(150), db.ForeignKey("user.username"))
    start_time = db.Column(db.DateTime(timezone=True))
    end_time = db.Column(db.DateTime(timezone=True))
    reason = db.Column(db.String(500))
