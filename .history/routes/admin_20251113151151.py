import os
from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Product, Category
from werkzeug.utils import secure_filename

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

UPLOAD_FOLDER = "static/images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------- HELPER: ADMIN CHECK -------------------
def admin_required(func):
    from functools import wraps
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        user = User.query.filter_by(username=identity).first()
        if not user or user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        return func(*args, **kwargs)
    return wrapper

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

# ------------------- ADMIN PAGES -------------------
@admin_bp.route("/")
@admin_required
def dashboard_redirect():
    return {"message": "Welcome to admin dashboard"}, 200

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
    return render_template("admin/products.html", products=products, categories=categories)

# ------------------- PRODUCTS API -------------------
@admin_bp.route("/api/products/<int:product_id>", methods=["GET"])
@admin_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product_to_dict(product)), 200

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

@admin_bp.route("/api/products/<int:product_id>", methods=["PATCH"])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Use form instead of JSON
    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")
    category_id = request.form.get("category_id")
    image = request.files.get("image")

    if name:
        product.name = name
    if price:
        try:
            product.price = float(price)
        except ValueError:
            return jsonify({"error": "Price must be a number"}), 400
    if stock:
        try:
            product.stock = int(stock)
        except ValueError:
            return jsonify({"error": "Stock must be an integer"}), 400
    if category_id:
        product.category_id = int(category_id)
    else:
        product.category_id = None

    # Handle image update
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        image.save(os.path.join(UPLOAD_FOLDER, filename))
        # Delete old image
        if product.image:
            old_path = os.path.join(UPLOAD_FOLDER, product.image)
            if os.path.exists(old_path):
                os.remove(old_path)
        product.image = filename

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

# -------------------
# GET ALL USERS
# -------------------
@admin_bp.route("/api/users", methods=["GET"])
@jwt_required()
def get_users():
    identity = get_jwt_identity()
    current_user = User.query.get(identity)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    users = User.query.all()
    result = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active
        } for u in users
    ]
    return jsonify(result), 200


# -------------------
# GET SINGLE USER
# -------------------
@admin_bp.route("/api/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    identity = get_jwt_identity()
    current_user = User.query.get(identity)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }), 200


# -------------------
# UPDATE USER ROLE / STATUS
# -------------------
@admin_bp.route("/api/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    identity = get_jwt_identity()
    current_user = User.query.get(identity)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    if current_user.id == user_id:
        return jsonify({"error": "You cannot change your own role/status"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    role = data.get("role")
    is_active = data.get("is_active")

    if role in ["user", "admin"]:
        user.role = role
    if isinstance(is_active, bool):
        user.is_active = is_active

    db.session.commit()
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }), 200


# -------------------
# DELETE USER
# -------------------
@admin_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    identity = get_jwt_identity()
    current_user = User.query.get(identity)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    if current_user.id == user_id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200