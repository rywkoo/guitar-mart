from flask import request, jsonify
from models import User, ResetToken
from extensions import db
from flask import Blueprint

reset_bp = Blueprint("reset", __name__)

@reset_bp.route("/request", methods=["POST"])
def request_reset():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No user found with this email"}), 404

    token = ResetToken.generate_token()
    token_hash = ResetToken.hash_token(token)

    reset_entry = ResetToken(user_id=user.id, token_hash=token_hash)
    db.session.add(reset_entry)
    db.session.commit()

    # send email logic here...
    from app import send_email
    subject = "Your Mini Mart Password Reset Token"
    body = f"Hello {user.username},\n\nYour password reset token is: {token}\nIt will expire in 15 minutes."
    send_email(user.email, subject, body)

    return jsonify({"message": "Reset token sent!"}), 200


@reset_bp.route("/verify", methods=["POST"])
def verify_token():
    """Check if the token is valid for a given email."""
    data = request.get_json()
    email = data.get("email")
    token = data.get("token")

    if not email or not token:
        return jsonify({"error": "Email and token are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No user found with this email"}), 404

    reset_entry = ResetToken.query.filter_by(user_id=user.id, used=False).order_by(ResetToken.created_at.desc()).first()
    if not reset_entry:
        return jsonify({"error": "No valid reset token found"}), 400

    if reset_entry.is_expired():
        return jsonify({"error": "Token has expired"}), 400

    if reset_entry.token_hash != ResetToken.hash_token(token):
        return jsonify({"error": "Invalid token"}), 400

    return jsonify({"message": "Token is valid"}), 200


@reset_bp.route("/reset", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    token = data.get("token")
    new_password = data.get("new_password")

    if not email or not token or not new_password:
        return jsonify({"error": "Email, token and new password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No user found with this email"}), 404

    reset_entry = ResetToken.query.filter_by(user_id=user.id, used=False).order_by(ResetToken.created_at.desc()).first()
    if not reset_entry:
        return jsonify({"error": "No valid reset token found"}), 400

    if reset_entry.is_expired():
        return jsonify({"error": "Token has expired"}), 400

    if reset_entry.token_hash != ResetToken.hash_token(token):
        return jsonify({"error": "Invalid token"}), 400

    user.set_password(new_password)
    reset_entry.used = True
    db.session.commit()

    return jsonify({"message": "Password has been reset successfully!"}), 200
