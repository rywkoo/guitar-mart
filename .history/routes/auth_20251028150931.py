# routes/auth.py
from flask import Blueprint, request, jsonify, make_response
from extensions import db
from models import User
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
    jwt_required,
    get_jwt_identity
)
from flask import Blueprint, make_response, redirect

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
        set_access_cookies(resp, token)  # <-- sets JWT cookie
        return resp
    return jsonify({"error": "Invalid credentials"}), 401



@auth_bp.route("/logout", methods=["GET"])
def logout():
    resp = make_response(redirect("/"))  # redirect to homepage
    unset_jwt_cookies(resp)              # remove JWT cookie
    return resp

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": user.username,
        "role": user.role
    })