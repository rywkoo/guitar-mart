# reset.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import User, ResetToken
from extensions import db
import hashlib

reset_bp = Blueprint("reset", __name__, url_prefix="/reset")


@reset_bp.route("/request", methods=["POST"])
def request_reset():
    """
    Request a password reset.
    Expects JSON: { "email": "user@example.com" }
    """
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Generate token
    token = ResetToken.generate_token()
    token_hash = ResetToken.hash_token(token)

    # Save hashed token
    reset_token = ResetToken(user_id=user.id, token_hash=token_hash)
    db.session.add(reset_token)
    db.session.commit()

    # TODO: Send token via email
    print(f"Reset token for {email}: {token}")  # For testing

    return jsonify({"message": "Reset token sent"})


@reset_bp.route("/verify", methods=["POST"])
def verify_token():
    """
    Verify reset token.
    Expects JSON: { "email": "...", "token": "123456" }
    """
    data = request.get_json()
    email = data.get("email")
    token = data.get("token")

    if not email or not token:
        return jsonify({"error": "Email and token required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    token_hash = ResetToken.hash_token(token)
    reset_token = ResetToken.query.filter_by(user_id=user.id, token_hash=token_hash, used=False).first()

    if not reset_token:
        return jsonify({"error": "Invalid token"}), 400

    if reset_token.is_expired():
        return jsonify({"error": "Token expired"}), 400

    return jsonify({"message": "Token is valid"})


@reset_bp.route("/reset", methods=["POST"])
def reset_password():
    """
    Reset password using a valid token.
    Expects JSON: { "email": "...", "token": "123456", "new_password": "..." }
    """
    data = request.get_json()
    email = data.get("email")
    token = data.get("token")
    new_password = data.get("new_password")

    if not all([email, token, new_password]):
        return jsonify({"error": "Email, token, and new password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    token_hash = ResetToken.hash_token(token)
    reset_token = ResetToken.query.filter_by(user_id=user.id, token_hash=token_hash, used=False).first()

    if not reset_token or reset_token.is_expired():
        return jsonify({"error": "Invalid or expired token"}), 400

    # Update password
    user.set_password(new_password)
    reset_token.used = True
    db.session.commit()

    return jsonify({"message": "Password reset successful"})
