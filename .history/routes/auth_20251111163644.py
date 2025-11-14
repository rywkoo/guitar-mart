# routes/auth.py
from flask import Blueprint, request, jsonify, make_response, redirect
from extensions import db, mail
from models import User, LoginToken, RegisterToken
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity
)
from flask_mail import Message
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__)  # NO url_prefix → /login, /login/verify


# -------------------
# HELPERS
# -------------------
def generate_token(length=6):
    return ''.join(secrets.choice("0123456789") for _ in range(length))


def send_email(subject, recipients, body):
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        sender="no-reply@minimart.kh"
    )
    mail.send(msg)


# -------------------
# SEND REGISTER TOKEN
# -------------------
@auth_bp.route("/send_register_token", methods=["POST"])
def send_register_token():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    token = secrets.token_hex(3).upper()

    existing = RegisterToken.query.filter_by(email=email).first()
    if existing:
        existing.token = token
        existing.expires_at = datetime.utcnow() + timedelta(minutes=10)
    else:
        new_token = RegisterToken(email=email, token=token, expires_at=datetime.utcnow() + timedelta(minutes=10))
        db.session.add(new_token)
    db.session.commit()

    send_email(
        subject="Mini Mart Registration Code",
        recipients=[email],
        body=f"Your registration code is: {token}\n\nIt expires in 10 minutes.\n\n- Mini Mart Team"
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
    token = data.get("token", "").strip().upper()

    if not all([username, email, password, token]):
        return jsonify({"error": "All fields are required"}), 400

    # Verify token
    token_entry = RegisterToken.query.filter_by(email=email, token=token).first()
    if not token_entry or token_entry.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired verification token"}), 400

    # Check duplicates
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    # Create user
    new_user = User(username=username, email=email, role="user", is_active=True)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.delete(token_entry)
    db.session.commit()

    return jsonify({"message": "Account created successfully"}), 201


# -------------------
# LOGIN: SEND TOKEN
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

    # Generate & save login token
    login_token = LoginToken.generate(user)

    send_email(
        subject="Your Mini Mart Login Code",
        recipients=[user.email],
        body=f"Hello {user.username},\n\nYour login code is: {login_token.token}\n\n"
             f"It expires in 10 minutes.\n\n"
             f"If you didn't request this, ignore this email.\n\n"
             f"- Mini Mart KH"
    )

    return jsonify({"message": "Login code sent to your email"}), 200


# -------------------
# LOGIN: VERIFY TOKEN
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

    set_access_cookies(resp, access_token)

    # Clean up
    db.session.delete(login_token)
    db.session.commit()

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