from flask import Blueprint, request, jsonify
from extensions import db
from models import User, ResetToken
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import secrets

reset_bp = Blueprint("reset", __name__)

# Step 1: Request reset token
@reset_bp.route("/request", methods=["POST"])
def request_reset():
    data = request.get_json()
    email = data.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Generate a secure random token
    token = secrets.token_urlsafe(16)

    # Save token in DB
    reset_entry = ResetToken(
        user_id=user.id,
        token=token,
        created_at=datetime.utcnow(),
        used=False
    )
    db.session.add(reset_entry)
    db.session.commit()

    # Return the token for testing (normally send via email)
    return jsonify({"reset_token": token}), 200


# Step 2: Confirm reset
@reset_bp.route("/confirm", methods=["POST"])
def confirm_reset():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("password")

    # Find the token entry
    reset_entry = ResetToken.query.filter_by(token=token).first()
    if not reset_entry:
        return jsonify({"msg": "Invalid token"}), 400

    if reset_entry.used:
        return jsonify({"msg": "Token already used"}), 400

    if reset_entry.is_expired():
        return jsonify({"msg": "Token expired"}), 400

    # Reset the user’s password
    user = User.query.get(reset_entry.user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.set_password(new_password)
    reset_entry.used = True  # mark token as used
    db.session.commit()

    return jsonify({"msg": "Password has been reset successfully"}), 200
