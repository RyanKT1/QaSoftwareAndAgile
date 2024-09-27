"""
This module handles the view-related routes for the web application. It includes a
route for rendering the home page and differentiates between admin and standard users.
"""

from datetime import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Reservation

views_blueprint = Blueprint("views", __name__)


@views_blueprint.route("/")
@login_required
def home():
    """
    Renders the home page based on the user's role (admin or standard user).
    """
    user_reservations = Reservation.query.filter_by(
        username=current_user.username
    ).all()

    # Check which reservations are ending within the next hour
    now = datetime.now()
    current_reservations = []
    upcoming_reservations = []
    for reservation in user_reservations:
        if reservation.start_time < now < reservation.end_time:
            current_reservations.append(reservation)
        elif len(upcoming_reservations) < 3:
            upcoming_reservations.append(reservation)
    return render_template(
        "home.html",
        user=current_user,
        upcoming_reservations=upcoming_reservations,
        current_reservations=current_reservations,
    )
