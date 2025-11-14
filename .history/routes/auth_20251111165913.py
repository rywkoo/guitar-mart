# routes/auth.py
from flask import Blueprint, request, jsonify, make_response, redirect
from extensions import db, mail
from models import User, LoginToken
from flask_jwt_extended import create_access_token, set_access_cookies
from flask_mail import Message
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

def send_email(subject, recipients, body):
    msg = Message(subject, recipients=recipients, body=body, sender="no-reply@minimart.kh")
    mail.send(msg)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active:
        return jsonify({"error": "Account disabled"}), 403

    login_token = LoginToken.generate(user)
    send_email(
        subject="Your Mini Mart Login Code",
        recipients=[user.email],
        body=f"Your 6-digit code: {login_token.token}\n\nExpires in 10 minutes.\n\n- Mini Mart KH"
    )
    return jsonify({"message": "Code sent to email"}), 200


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
        return jsonify({"error": "Invalid or expired code"}), 400

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
    set_access_cookies(resp, access_token)  # HTTP-only cookie
    db.session.delete(login_token)
    db.session.commit()
    return resp, 200