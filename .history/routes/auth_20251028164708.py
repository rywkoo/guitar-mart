from flask import Blueprint, request, jsonify, make_response
from extensions import db, mail
from models import User, LoginToken
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required

from flask_mail import Message
import random, string
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__)

# Helper to generate random token
def generate_token(length=6):
    return ''.join(random.choices(string.digits, k=length))

# -------------------
# REGISTER WITH EMAIL TOKEN
# -------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email exists"}), 400

    # Create user but inactive until token verified
    user = User(
        username=data["username"],
        email=data["email"],
        role=data.get("role", "user"),
        is_active=False
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    # Generate verification token
    token = generate_token()
    login_token = LoginToken(user_id=user.id, token=token, expires_at=datetime.utcnow()+timedelta(minutes=10))
    db.session.add(login_token)
    db.session.commit()

    # Send email
    msg = Message("Verify your account", recipients=[user.email])
    msg.body = f"Your account verification token is: {token}"
    mail.send(msg)

    return jsonify({"message": "Verification token sent to email"}), 200

@auth_bp.route("/register/verify", methods=["POST"])
def register_verify():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    token_entry = LoginToken.query.filter_by(user_id=user.id, token=data["token"]).first()
    if not token_entry or token_entry.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400

    # Activate user and remove token
    user.is_active = True
    db.session.delete(token_entry)
    db.session.commit()

    # Create JWT
    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({
        "message": "Registration successful",
        "access_token": access_token,
        "username": user.username,
        "role": user.role
    })

# -------------------
# LOGIN WITH EMAIL TOKEN
# -------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active:
        return jsonify({"error": "Account not verified. Check your email."}), 403

    # Generate login token
    token = generate_token()
    login_token = LoginToken(user_id=user.id, token=token, expires_at=datetime.utcnow()+timedelta(minutes=10))
    db.session.add(login_token)
    db.session.commit()

    # Send token via email
    msg = Message("Your login token", recipients=[user.email])
    msg.body = f"Your login token is: {token}"
    mail.send(msg)

    return jsonify({"message": "Login token sent to email"}), 200

@auth_bp.route("/login/verify", methods=["POST"])
def login_verify():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    token_entry = LoginToken.query.filter_by(user_id=user.id, token=data["token"]).first()
    if not token_entry or token_entry.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400

    # Remove token and issue JWT
    db.session.delete(token_entry)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({
        "access_token": access_token,
        "username": user.username,
        "role": user.role
    })


@auth_bp.route("/logout", methods=["GET"])
def logout():
    resp = make_response(redirect("/"))  # redirect to homepage
    unset_jwt_cookies(resp)              # remove JWT cookie
    return resp

@auth_bp.route("/me", methods=["GET"])
@jwt_required()  # This requires a valid JWT cookie
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