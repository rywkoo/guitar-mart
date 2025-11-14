# routes/auth.py
from flask import Blueprint, request, jsonify, make_response, redirect
from extensions import db, mail
from models import User, LoginToken, RegisterToken, ResetToken
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity
)
from flask_mail import Message
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint("auth", __name__)

# -------------------
# HELPERS
# -------------------
def send_email(subject, recipients, body):
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        sender="no-reply@minimart.kh"
    )
    mail.send(msg)


# -------------------
# SEND REGISTER TOKEN (6-digit)
# -------------------
@auth_bp.route("/send_register_token", methods=["POST"])
def send_register_token():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Generate 6-digit token
    token = RegisterToken.generate(email)

    send_email(
        subject="Mini Mart Registration Code",
        recipients=[email],
        body=f"Hello!\n\n"
             f"Your registration code is: {token}\n\n"
             f"It expires in 10 minutes.\n\n"
             f"Use it to complete your account.\n\n"
             f"- Mini Mart KH"
    )

    return jsonify({"message": "Verification code sent to your email"}), 200


# -------------------
# REGISTER USER
# -------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    token = data.get("token", "").strip()

    if not all([username, email, password, token]):
        return jsonify({"error": "All fields are required"}), 400

    # Verify 6-digit token
    if not RegisterToken.verify(email, token):
        return jsonify({"error": "Invalid or expired verification code"}), 400

    # Check duplicates
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    # Create user
    new_user = User(username=username, email=email, role="user", is_active=True)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Account created successfully"}), 201


# -------------------
# LOGIN: SEND 6-DIGIT TOKEN
# -------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    # Generate 6-digit login token
    login_token = LoginToken.generate(user)

    send_email(
        subject="Your Mini Mart Login Code",
        recipients=[user.email],
        body=f"Hello {user.username}!\n\n"
             f"Your login code is: {login_token.token}\n\n"
             f"It expires in 10 minutes.\n\n"
             f"If you didn't request this, ignore it.\n\n"
             f"- Mini Mart KH"
    )

    return jsonify({"message": "Login code sent to your email"}), 200


# -------------------
# LOGIN: VERIFY 6-DIGIT TOKEN
# -------------------
@auth_bp.route("/login/verify", methods=["POST"])
def login_verify():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    token = data.get("token", "").strip()

    if not username or not token:
        return jsonify({"error": "Username and token required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Verify token
    login_token = LoginToken.query.filter_by(user_id=user.id, token=token).first()
    if not login_token or login_token.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired login code"}), 400

    # Issue JWT
    access_token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role}
    )

    resp = jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "username": user.username,
        "role": user.role
    })
set_access_cookies(resp, access_token)  # This sets HTTP-only cookie
return resp, 200


# -------------------
# LOGOUT
# -------------------
@auth_bp.route("/logout", methods=["GET"])
@jwt_required()
def logout():
    resp = make_response(redirect("/"))
    unset_jwt_cookies(resp)
    return resp


# -------------------
# CURRENT USER (Protected)
# -------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }), 200


# -------------------
# PASSWORD RESET: SEND TOKEN
# -------------------
@auth_bp.route("/reset/request", methods=["POST"])
def reset_request():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # Still say "sent" to prevent email enumeration
        return jsonify({"message": "If your email exists, a reset code was sent"}), 200

    # Generate 6-digit reset token
    token = ResetToken.create_for_user(user)

    send_email(
        subject="Mini Mart Password Reset",
        recipients=[email],
        body=f"Hello {user.username}!\n\n"
             f"Your password reset code is: {token}\n\n"
             f"It expires in 15 minutes.\n\n"
             f"Use it on the reset page.\n\n"
             f"- Mini Mart KH"
    )

    return jsonify({"message": "If your email exists, a reset code was sent"}), 200


# -------------------
# PASSWORD RESET: VERIFY & CHANGE
# -------------------
@auth_bp.route("/reset/verify", methods=["POST"])
def reset_verify():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "")

    if not all([email, token, new_password]):
        return jsonify({"error": "All fields required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid request"}), 400

    # Verify hashed token
    token_hash = ResetToken.hash_token(token)
    reset_token = ResetToken.query.filter_by(user_id=user.id, token_hash=token_hash).first()
    if not reset_token or reset_token.used or reset_token.is_expired():
        return jsonify({"error": "Invalid or expired reset code"}), 400

    # Update password
    user.set_password(new_password)
    reset_token.used = True
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200