# routes/admin.py
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from extensions import db
from models import User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# -----------------------------
# Admin Dashboard Pages
# -----------------------------
@admin_bp.route("/")
@jwt_required()
def admin_index():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return "Method Not Allowed", 405
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/dashboard")
@jwt_required()
def dashboard():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return "Method Not Allowed", 405
    return render_template("admin/dashboard.html")

# -----------------------------
# Admin API Routes
# -----------------------------

@admin_bp.route("/check", methods=["GET"])
@jwt_required()
def check_admin():
    """Check if current user is admin"""
    identity = get_jwt_identity()
    user = User.query.get(identity)
    if not user or user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "username": user.username,
        "role": user.role
    }), 200


# Get all users
@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def get_all_users():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    users = User.query.all()
    user_list = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active
    } for u in users]

    return jsonify(user_list), 200


# Delete user by ID
@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Prevent deleting self
    if user.id == get_jwt_identity():
        return jsonify({"error": "You cannot delete your own account"}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"User '{user.username}' deleted successfully"}), 200


# Update user role or activation
@admin_bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"message": f"User '{user.username}' updated successfully"}), 200

@admin_bp.route("/dashboard")
@jwt_required()
def dashboard():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return "Method Not Allowed", 405
    return render_template("admin/dashboard.html")

