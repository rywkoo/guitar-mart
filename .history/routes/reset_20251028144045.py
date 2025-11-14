from flask import Blueprint, request, jsonify
from models import User, ResetToken
from extensions import db
from datetime import datetime
from app import send_email  # assuming send_email exists in app.py

reset_bp = Blueprint("reset", __name__)

# --- Helper functions ---
def generate_reset_token(user):
    token = ResetToken.generate_token()
    token_hash = ResetToken.hash_token(token)

    reset_entry = ResetToken(user_id=user.id, token_hash=token_hash)
    db.session.add(reset_entry)
    db.session.commit()
    return token

# --- Routes ---

@reset_bp.route("/request", methods=["POST"])
def request_reset():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"msg": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "No user found with this email"}), 404

    token = generate_reset_token(user)

    # Send email
    subject = "Your Mini Mart Password Reset Token"
    body = f"Hello {user.username},\n\nYour password reset token is: {token}\nIt will expire in 15 minutes."
    send_email(user.email, subject, body)

    return jsonify({"msg": "Reset token sent!", "reset_token": token}), 200


@reset_bp.route("/reset", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not email or not token or not new_password or not confirm_password:
        return jsonify({"msg": "Email, token, and both passwords are required"}), 400

    if new_password != confirm_password:
        return jsonify({"msg": "Passwords do not match"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "No user found with this email"}), 404

    reset_entry = ResetToken.query.filter_by(user_id=user.id, used=False).order_by(ResetToken.created_at.desc()).first()
    if not reset_entry:
        return jsonify({"msg": "No valid reset token found"}), 400

    if reset_entry.is_expired():
        return jsonify({"msg": "Token has expired"}), 400

    if reset_entry.token_hash != ResetToken.hash_token(token):
        return jsonify({"msg": "Invalid token"}), 400

    # Update password
    user.set_password(new_password)
    reset_entry.used = True
    db.session.commit()

    return jsonify({"msg": "Password has been reset successfully!"}), 200
