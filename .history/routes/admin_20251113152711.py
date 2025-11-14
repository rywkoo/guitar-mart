# routes/admin.py
from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Product, Category
import os

admin_bp = Blueprint("admin", __name__)

# -------------------
# HELPERS
# -------------------
def admin_required(fn):
    """Decorator to ensure the JWT user is admin."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def save_image(file):
    """Save uploaded image and return filename."""
    if not file:
        return None
    filename = secure_filename(file.filename)
    path = os.path.join("static/images", filename)
    file.save(path)
    return filename

# -------------------
# DASHBOARD / ADMIN PAGES
# -------------------
@admin_bp.route("/admin/products")
@jwt_required()
@admin_required
def admin_products_page():
    categories = Category.query.all()
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/products.html", products=products, categories=categories)

@admin_bp.route("/admin/users")
@jwt_required()
@admin_required
def admin_users_page():
    return render_template("admin/users.html")

# -------------------
# PRODUCTS API
# -------------------
@admin_bp.route("/admin/api/products", methods=["GET"])
@jwt_required()
@admin_required
def get_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "price": float(p.price),
        "stock": p.stock,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else None,
        "image": p.image
    } for p in products]), 200

@admin_bp.route("/admin/api/products/<int:product_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_product(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify({
        "id": p.id,
        "name": p.name,
        "price": float(p.price),
        "stock": p.stock,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else None,
        "image": p.image
    }), 200

@admin_bp.route("/admin/api/products", methods=["POST"])
@jwt_required()
@admin_required
def add_product():
    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")
    category_id = request.form.get("category_id") or None
    image_file = request.files.get("image")

    if not all([name, price, stock]):
        return jsonify({"error": "Name, price, and stock are required"}), 400

    image_filename = save_image(image_file)
    product = Product(
        name=name,
        price=float(price),
        stock=int(stock),
        category_id=int(category_id) if category_id else None,
        image=image_filename
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "Product added", "product": {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else None,
        "image": product.image
    }}), 201

@admin_bp.route("/admin/api/products/<int:product_id>", methods=["PATCH"])
@jwt_required()
@admin_required
def update_product(product_id):
    p = Product.query.get_or_404(product_id)
    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")
    category_id = request.form.get("category_id")
    image_file = request.files.get("image")

    if name: p.name = name
    if price: p.price = float(price)
    if stock: p.stock = int(stock)
    if category_id: p.category_id = int(category_id)
    if image_file: p.image = save_image(image_file)

    db.session.commit()
    return jsonify({"message": "Product updated", "product": {
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "stock": p.stock,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else None,
        "image": p.image
    }}), 200

@admin_bp.route("/admin/api/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_product(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": f"Product {p.name} deleted"}), 200

# -------------------
# USERS API
# -------------------
@admin_bp.route("/admin/api/users", methods=["GET"])
@jwt_required()
@admin_required
def get_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active
    } for u in users]), 200

@admin_bp.route("/admin/api/users/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_user(user_id):
    u = User.query.get_or_404(user_id)
    return jsonify({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active
    }), 200

@admin_bp.route("/admin/api/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
@admin_required
def update_user(user_id):
    u = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    role = data.get("role")
    is_active = data.get("is_active")

    if role in ["user", "admin"]:
        u.role = role
    if isinstance(is_active, bool):
        u.is_active = is_active

    db.session.commit()
    return jsonify({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active
    }), 200

@admin_bp.route("/admin/api/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id):
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"message": f"User {u.username} deleted"}), 200


@admin_bp.route("/admin/api/reports/purchases")
@jwt_required()
@admin_required
def purchase_report():
    """
    Returns purchase totals for dashboard analytics.
    Supports:
      - daily: ?period=daily&date=YYYY-MM-DD
      - weekly: ?period=weekly&start=YYYY-MM-DD&end=YYYY-MM-DD
      - monthly: ?period=monthly&year=YYYY&month=MM
      - custom: ?period=custom&start=YYYY-MM-DD&end=YYYY-MM-DD
      - filter by username: ?username=...
    """
    period = request.args.get("period", "daily")
    username = request.args.get("username", None)

    query = Invoice.query

    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "Username not found"}), 404
        query = query.filter(Invoice.username == username)

    invoices = []

    if period == "daily":
        date_str = request.args.get("date")
        if not date_str:
            return jsonify({"error": "Missing date"}), 400
        try:
            day = func.strftime("%Y-%m-%d", date_str)
        except:
            return jsonify({"error": "Invalid date"}), 400

        invoices = query.filter(cast(Invoice.created_at, Date) == date_str).all()

    elif period == "weekly" or period == "custom":
        start = request.args.get("start")
        end = request.args.get("end")
        if not start or not end:
            return jsonify({"error": "Missing start or end date"}), 400
        invoices = query.filter(
            cast(Invoice.created_at, Date).between(start, end)
        ).all()

    elif period == "monthly":
        year = request.args.get("year")
        month = request.args.get("month")
        if not year or not month:
            return jsonify({"error": "Missing year or month"}), 400
        invoices = query.filter(
            func.strftime("%Y", Invoice.created_at) == year,
            func.strftime("%m", Invoice.created_at) == month.zfill(2)
        ).all()

    else:
        return jsonify({"error": "Invalid period"}), 400

    # return total amount and invoice count
    total_amount = sum(i.total_amount for i in invoices)
    count = len(invoices)

    return jsonify({
        "count": count,
        "total_amount": total_amount,
        "invoices": [dict(
            id=i.id,
            username=i.username,
            total_amount=i.total_amount,
            created_at=i.created_at.isoformat()
        ) for i in invoices]
    })