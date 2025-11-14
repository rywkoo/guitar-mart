from flask import Blueprint, request, jsonify
from extensions import db
from models import User
from flask_jwt_extended import create_access_token, decode_token
from datetime import timedelta

reset_bp = Blueprint("reset", __name__)

# Step 1: User requests password reset
@reset_bp.route("/request", methods=["POST"])
def request_reset():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Create a short-lived reset token (valid for 15 minutes)
    reset_token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=15))

    # Normally we’d email this. But we’ll just return it for now
    return jsonify({"reset_token": reset_token}), 200


# Step 2: User submits new password with reset token
@reset_bp.route("/confirm", methods=["POST"])
def confirm_reset():
    data = request.get_json()
    reset_token = data.get("token")
    new_password = data.get("password")

    try:
        decoded = decode_token(reset_token)
        user_id = decoded["sub"]
    except Exception:
        return jsonify({"msg": "Invalid or expired token"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.password = new_password  # hash this if you use hashing
    db.session.commit()

    return jsonify({"msg": "Password has been reset successfully"}), 200
