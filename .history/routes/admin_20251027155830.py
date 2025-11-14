from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Product

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# /admin endpoint
@admin_bp.route("/")
@jwt_required()
def index():
    user_id = get_jwt_identity()  # get current user id from JWT
    user = User.query.get(user_id)

    if user.role == "admin":
        # Admins are redirected to dashboard
        return redirect(url_for("admin.dashboard"))
    else:
        # Normal users cannot access /admin
        return "Method not allowed", 403

@admin_bp.route("/dashboard")
@jwt_required()
def dashboard():
    return render_template("admin/dashboard.html")

@admin_bp.route("/products")
@jwt_required()
def products():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.role != "admin":
        return "Method not allowed", 403

    products = Product.query.all()
    return render_template("admin/products.html", products=products)
