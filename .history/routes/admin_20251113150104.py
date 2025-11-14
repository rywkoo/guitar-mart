# routes/admin.py
# Mini Mart KH - Admin Panel (JWT & ADMIN PROTECTED)
# @rywkoo | November 13, 2025 | Cambodia (KH)

import os
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Product, Category

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

UPLOAD_FOLDER = "static/images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


# -----------------------------
# HELPERS
# -----------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def product_to_dict(product):
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "image": product.image,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else None
    }


# -----------------------------
# ADMIN CHECK DECORATOR
# -----------------------------
def admin_required(fn):
    """Protect routes: require JWT + admin role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = User.query.get(get_jwt_identity())
            if not current_user or current_user.role != "admin":
                return jsonify({"error": "Forbidden"}), 403
        except Exception:
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


# -----------------------------
# ADMIN PAGES
# -----------------------------
@admin_bp.route("/")
@admin_required
def admin_index():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")


@admin_bp.route("/users")
@admin_required
def users_page():
    return render_template("admin/users.html")


@admin_bp.route("/products")
@admin_required
def products_page():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template(
        "admin/products.html",
        products=products,
        categories=categories
    )


# -----------------------------
# JWT CHECK API
# -----------------------------
@admin_bp.route("/check", methods=["GET"])
@admin_required
def check_admin():
    current_user = User.query.get(get_jwt_identity())
    return jsonify({"username": current_user.username, "role": current_user.role}), 200


# -----------------------------
# USERS API
# -----------------------------
@admin_bp.route("/api/users", methods=["GET"])
@admin_required
def get_all_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active
        } for u in users
    ]), 200


@admin_bp.route("/api/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }), 200


@admin_bp.route("/api/users/<int:user_id>", methods=["PATCH"])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"message": f"User '{user.username}' updated"}), 200


@admin_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.id == user_id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User '{user.username}' deleted"}), 200


# -----------------------------
# PRODUCTS API
# -----------------------------
@admin_bp.route("/api/products/", methods=["POST"])
@admin_required
def add_product():
    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")
    category_id = request.form.get("category_id")
    image = request.files.get("image")

    if not all([name, price, stock]):
        return jsonify({"error": "Missing required fields"}), 400

    filename = None
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        image.save(os.path.join(UPLOAD_FOLDER, filename))

    product = Product(
        name=name,
        price=float(price),
        stock=int(stock),
        category_id=int(category_id) if category_id else None,
        image=filename
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({"success": True, "product": product_to_dict(product)}), 201


@admin_bp.route("/api/products/<int:product_id>", methods=["GET"])
@admin_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product_to_dict(product)), 200


@admin_bp.route("/api/products/<int:product_id>", methods=["PATCH"])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if "name" in data:
        product.name = str(data["name"])
    if "price" in data:
        try:
            product.price = float(data["price"])
        except ValueError:
            return jsonify({"error": "Price must be a number"}), 400
    if "stock" in data:
        try:
            product.stock = int(data["stock"])
        except ValueError:
            return jsonify({"error": "Stock must be an integer"}), 400
    if "category_id" in data:
        product.category_id = int(data["category_id"]) if data["category_id"] else None

    # Skip image for simplicity

    db.session.commit()
    return jsonify({"success": True, "product": product_to_dict(product)}), 200


@admin_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.image:
        path = os.path.join(UPLOAD_FOLDER, product.image)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(product)
    db.session.commit()
    return jsonify({"success": True, "message": "Product deleted"}), 200

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = User.query.get(get_jwt_identity())
            print("JWT ID:", get_jwt_identity())
            print("Current user:", current_user)
            print("Role:", getattr(current_user, "role", None))
            if not current_user or current_user.role != "admin":
                return jsonify({"error": "Forbidden"}), 403
        except Exception as e:
            print("JWT Error:", e)
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper
