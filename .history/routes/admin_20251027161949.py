# routes/admin.py
from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

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

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import User

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/check", methods=["GET"])
@jwt_required()  # require JWT cookie
def check_admin():
    identity = get_jwt_identity()
    user = User.query.get(identity)
    if not user or user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "username": user.username,
        "role": user.role
    })
