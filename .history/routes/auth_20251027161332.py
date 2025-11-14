from flask import Blueprint, request, jsonify
from extensions import db
from models import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email exists"}), 400

    user = User(
        username=data["username"],
        email=data["email"],
        role=data.get("role", "user")  # default to user
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created successfully"})


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()
    if user and user.check_password(data["password"]):
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        resp = make_response(jsonify({"message": "Login successful"}))
        # Set JWT in cookie
        set_access_cookies(resp, token)
        return resp
    return jsonify({"error": "Invalid credentials"}), 401

# routes/auth.py
from flask_jwt_extended import unset_jwt_cookies

@auth_bp.route("/logout", methods=["POST"])
def logout():
    resp = make_response(jsonify({"message": "Logout successful"}))
    unset_jwt_cookies(resp)
    return resp
