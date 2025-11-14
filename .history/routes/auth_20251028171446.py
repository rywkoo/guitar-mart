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
    if existing:
        existing.token = token
        existing.expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    else:
        new_token = RegisterToken(email=email, token=token,
                                  expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=10))
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
from flask import request, jsonify
from app import app, db
from models import User, RegisterToken
from flask_mail import Message
from app import mail

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    verify_code = data.get('verify_code')  # will be sent by email

    # Step 1: Verify token
    if not RegisterToken.verify(email, verify_code):
        return jsonify({'error': 'Invalid or expired verification code'}), 400

    # Step 2: Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    # Step 3: Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Optionally delete used token
    token_obj = RegisterToken.query.filter_by(email=email, token=verify_code).first()
    db.session.delete(token_obj)
    db.session.commit()

    return jsonify({'message': 'Account created successfully!'})


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
    data = request.json
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

    # Delete token so it can't be reused
    db.session.delete(login_token)
    db.session.commit()

    return resp



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