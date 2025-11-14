from flask import Blueprint, request, jsonify, make_response, redirect
from extensions import db, mail
from models import User, LoginToken, RegisterToken, ResetToken
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity
)
from flask_mail import Message
from datetime import datetime
import secrets

auth_bp = Blueprint("auth", __name__)

# ------------------- HELPERS -------------------
def send_email(subject, recipients, body):
    msg = Message(subject=subject, recipients=recipients, body=body, sender="no-reply@minimart.kh")
    mail.send(msg)

# ------------------- REGISTER -------------------
@auth_bp.route("/send_register_token", methods=["POST"])
def send_register_token():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    token = RegisterToken.generate(email)
    send_email(
        subject="Mini Mart Registration Code",
        recipients=[email],
        body=f"Your registration code is: {token}\nIt expires in 10 minutes."
    )
    return jsonify({"message": "Verification code sent to your email"}), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    token = data.get("token", "").strip()

    if not all([username, email, password, token]):
        return jsonify({"error": "All fields are required"}), 400

    if not RegisterToken.verify(email, token):
        return jsonify({"error": "Invalid or expired verification code"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    new_user = User(username=username, email=email, role="user", is_active=True)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Account created successfully"}), 201

# ------------------- LOGIN -------------------
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

    login_token = LoginToken.generate(user)
    send_email(
        subject="Your Mini Mart Login Code",
        recipients=[user.email],
        body=f"Hello {user.username}, your login code is: {login_token.token}\nExpires in 10 minutes."
    )

    return jsonify({"message": "Login code sent to your email"}), 200


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

    access_token = create_access_token(
        identity=str(user.username),  # ✅ Must be string
        additional_claims={"role": user.role}
    )

    resp = jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "username": user.username,
        "role": user.role
    })
    set_access_cookies(resp, access_token)

    db.session.delete(login_token)
    db.session.commit()
    return resp, 200


@auth_bp.route("/logout", methods=["GET"])
@jwt_required()
def logout():
    resp = make_response(redirect("/"))
    unset_jwt_cookies(resp)
    return resp


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }), 200


# ------------------- PASSWORD RESET -------------------
@auth_bp.route("/reset/request", methods=["POST"])
def reset_request():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        token = ResetToken.create_for_user(user)
        send_email(
            subject="Mini Mart Password Reset",
            recipients=[email],
            body=f"Hello {user.username}, your reset code is: {token}\nExpires in 15 minutes."
        )
    # Always return success
    return jsonify({"message": "If your email exists, a reset code was sent"}), 200


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

    token_hash = ResetToken.hash_token(token)
    reset_token = ResetToken.query.filter_by(user_id=user.id, token_hash=token_hash).first()
    if not reset_token or reset_token.used or reset_token.is_expired():
        return jsonify({"error": "Invalid or expired reset code"}), 400

    user.set_password(new_password)
    reset_token.used = True
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200
