# routes/admin.py
# Mini Mart KH - Admin Panel
# @rywkoo | November 13, 2025 | Cambodia (KH)

import os
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Product, Category

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

UPLOAD_FOLDER = "static/images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------
# Admin Pages
# -----------------------------
@admin_bp.route("/")
def admin_index():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
def dashboard():
    return render_template("admin/dashboard.html")


@admin_bp.route("/users")
def users_page():
    return render_template("admin/users.html")


@admin_bp.route("/products")
def products_page():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template(
        "admin/products.html",
        products=products,
        categories=categories
    )


# -----------------------------
# JWT-Protected Admin Check
# -----------------------------
@admin_bp.route("/check", methods=["GET"])
@jwt_required()
def check_admin():
    user = User.query.get(get_jwt_identity())
    if not user or user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({"username": user.username, "role": user.role}), 200


# -----------------------------
# USERS API
# -----------------------------
@admin_bp.route("/api/users", methods=["GET"])
def get_all_users():
    try:
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
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


@admin_bp.route("/api/users/<int:user_id>", methods=["GET"])
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
@jwt_required()
def update_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"message": f"User '{user.username}' updated"}), 200


@admin_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.id == get_jwt_identity():
        return jsonify({"error": "You cannot delete your own account"}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User '{user.username}' deleted"}), 200


# -----------------------------
# PRODUCTS API
# -----------------------------
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


@admin_bp.route("/api/products/", methods=["POST"])
@jwt_required()
def add_product():
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

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
@jwt_required()
def get_product(product_id):
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    product = Product.query.get_or_404(product_id)
    return jsonify(product_to_dict(product)), 200


@admin_bp.route("/api/products/<int:product_id>", methods=["PATCH"])
@jwt_required()
def edit_product(product_id):
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    product = Product.query.get_or_404(product_id)

    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")
    category_id = request.form.get("category_id")
    image = request.files.get("image")

    if name:
        product.name = name
    if price:
        product.price = float(price)
    if stock:
        product.stock = int(stock)
    if category_id:
        product.category_id = int(category_id)

    if image and allowed_file(image.filename):
        # Delete old image
        if product.image:
            old_path = os.path.join(UPLOAD_FOLDER, product.image)
            if os.path.exists(old_path):
                os.remove(old_path)
        filename = secure_filename(image.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        image.save(os.path.join(UPLOAD_FOLDER, filename))
        product.image = filename

    db.session.commit()
    return jsonify({"success": True, "product": product_to_dict(product)}), 200


@admin_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    product = Product.query.get_or_404(product_id)
    if product.image:
        path = os.path.join(UPLOAD_FOLDER, product.image)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(product)
    db.session.commit()
    return jsonify({"success": True, "message": "Product deleted"}), 200
