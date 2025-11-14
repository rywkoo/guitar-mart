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

auth_bp = Blueprint("auth", __name__)

# -------------------
# HELPERS
# -------------------
def generate_token(length=6):
    return ''.join(secrets.choice("0123456789") for _ in range(length))

def send_email(subject, recipients, body):
    msg = Message(subject=subject, recipients=recipients, body=body)
    mail.send(msg)

# -------------------
# REGISTER WITH EMAIL TOKEN
# -------------------

# Step 1: Send registration token
@auth_bp.route("/send_register_token", methods=["POST"])
def send_register_token():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Create a 6-digit token
    token = secrets.token_hex(3)  # 6 hex chars

    # Save token in DB with expiration
    existing = RegisterToken.query.filter_by(email=email).first()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    if existing:
        existing.token = token
        existing.expires_at = expires_at
    else:
        new_token = RegisterToken(email=email, token=token, expires_at=expires_at)
        db.session.add(new_token)
    db.session.commit()

    # Send email
    send_email(
        subject="Mini Mart Registration Code",
        recipients=[email],
        body=f"Your registration code is: {token}"
    )

    return jsonify({"message": "Verification code sent"}), 200


# Step 2: Register user with token verification
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    token = data.get("token")

    if not all([username, email, password, token]):
        return jsonify({"error": "All fields are required"}), 400

    # Verify token
    token_entry = RegisterToken.query.filter_by(email=email, token=token).first()
    if not token_entry or token_entry.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired verification token"}), 400

    # Check if user exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists"}), 400

    # Create user
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    new_user.is_active = True
    db.session.add(new_user)
    db.session.delete(token_entry)
    db.session.commit()

    return jsonify({"message": "Account created successfully"}), 201


# -------------------
# LOGIN WITH EMAIL TOKEN
# -------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    if not user.is_active:
        return jsonify({"error": "Account not verified"}), 403

    # Generate login token
    login_token = LoginToken.generate(user)

    # Send token to email
    msg = Message(
        subject="Your Mini Mart Login Token",
        recipients=[user.email],
        body=f"Your login token is: {login_token.token}\nIt expires in 10 minutes."
    )
    mail.send(msg)

    return jsonify({"message": "Login token sent to your email."})


@auth_bp.route("/login/verify", methods=["POST"])
def login_verify():
    data = request.get_json()
    username = data.get("username")
    token = data.get("token")

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    login_token = LoginToken.query.filter_by(user_id=user.id, token=token).first()
    if not login_token or login_token.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400

    # Issue JWT
    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    resp = jsonify({
        "message": "Login successful",
        "username": user.username,
        "role": user.role,
        "access_token": access_token
    })
    set_access_cookies(resp, access_token)

    # Delete token
    db.session.delete(login_token)
    db.session.commit()

    return resp


# -------------------
# LOGOUT
# -------------------

@auth_bp.route("/logout", methods=["GET"])
def logout():
    resp = make_response(redirect("/"))
    unset_jwt_cookies(resp)
    return resp


# -------------------
# CURRENT USER
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
        "role": user.role
    })
