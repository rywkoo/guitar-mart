# routes/admin.py
from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Product, Category, Invoice
from sqlalchemy import func
from datetime import datetime, timedelta
import os
from functools import wraps

admin_bp = Blueprint("admin", __name__)

# -------------------
# HELPERS
# -------------------
def admin_required(fn):
    """Decorator to ensure the JWT user is admin."""
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
# ADMIN PAGES
# -------------------
@admin_bp.route("/admin/dashboard")
@jwt_required()
@admin_required
def dashboard_page():
    return render_template("admin/dashboard.html")

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

# -------------------
# PURCHASE REPORTS
# -------------------
@admin_bp.route("/admin/api/reports/purchases", methods=["GET"])
@jwt_required()
@admin_required
def purchase_report():
    report_type = request.args.get("type", "daily")  # daily, weekly, monthly, custom
    username_filter = request.args.get("username", None)
    start_date = request.args.get("start", None)
    end_date = request.args.get("end", None)

    query = Invoice.query
    if username_filter:
        query = query.filter(Invoice.username.ilike(f"%{username_filter}%"))

    now = datetime.utcnow()

    labels = []
    totals = []

    if report_type == "daily":
        # Today: group by hour or just single total
        today_start = datetime(now.year, now.month, now.day)
        today_end = today_start + timedelta(days=1)
        query = query.filter(Invoice.created_at >= today_start, Invoice.created_at < today_end)
        total = sum(inv.total_amount for inv in query.all())
        labels = ["Today"]
        totals = [total]

    elif report_type == "weekly":
        # Last 7 days
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            start = datetime(day.year, day.month, day.day)
            end = start + timedelta(days=1)
            day_total = sum(inv.total_amount for inv in Invoice.query.filter(
                Invoice.created_at >= start,
                Invoice.created_at < end,
                Invoice.username.ilike(f"%{username_filter}%") if username_filter else True
            ).all())
            labels.append(start.strftime("%b %d"))
            totals.append(day_total)

    elif report_type == "monthly":
        # Last 30 days
        for i in range(29, -1, -1):
            day = now - timedelta(days=i)
            start = datetime(day.year, day.month, day.day)
            end = start + timedelta(days=1)
            day_total = sum(inv.total_amount for inv in Invoice.query.filter(
                Invoice.created_at >= start,
                Invoice.created_at < end,
                Invoice.username.ilike(f"%{username_filter}%") if username_filter else True
            ).all())
            labels.append(start.strftime("%b %d"))
            totals.append(day_total)

    elif report_type == "custom" and start_date and end_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            delta_days = (end_dt - start_dt).days + 1
            for i in range(delta_days):
                day = start_dt + timedelta(days=i)
                start = datetime(day.year, day.month, day.day)
                end = start + timedelta(days=1)
                day_total = sum(inv.total_amount for inv in Invoice.query.filter(
                    Invoice.created_at >= start,
                    Invoice.created_at < end,
                    Invoice.username.ilike(f"%{username_filter}%") if username_filter else True
                ).all())
                labels.append(start.strftime("%b %d"))
                totals.append(day_total)
        except Exception:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    return jsonify({"labels": labels, "totals": totals})

@admin_bp.route("/admin/api/invoices", methods=["GET"])
@jwt_required()
@admin_required
def get_all_invoices():
    """
    GET /admin/api/invoices
    Returns ALL invoices for dashboard (aggregated charts + list).
    """
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return jsonify([{
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "username": inv.username,
        "total_amount": float(inv.total_amount),
        "created_at": inv.created_at.isoformat()
    } for inv in invoices]), 200

@admin_bp.route("/admin/api/invoices/<int:invoice_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_single_invoice(invoice_id):
    """
    GET /admin/api/invoices/<id>
    Returns single invoice details (for user chart items if needed).
    """
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify({
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "username": invoice.username,
        "total_amount": float(invoice.total_amount),
        "created_at": invoice.created_at.isoformat(),
        "items": [{
            "id": item.id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "total_price": float(item.unit_price * item.quantity)
        } for item in invoice.items]
    }), 200

@admin_bp.route("/admin/categories")
@jwt_required()
def categories():
    cats = Category.query.all()
    return render_template('admin/category.html', categories=cats)


@admin_bp.route("/admin/api/categories", methods=["GET"])
@jwt_required()
@admin_required
def get_categories():
    cats = Category.query.all()
    return jsonify([c.to_dict() for c in cats]), 200

@admin_bp.route("/admin/api/categories", methods=["POST"])
@jwt_required()
@admin_required
def add_category():
    data = request.form
    if not data.get('name'):
        return jsonify({"error": "Name is required"}), 400
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({"error": "Category already exists"}), 400

    cat = Category(name=data['name'], description=data.get('description'))
    db.session.add(cat)
    db.session.commit()
    return jsonify({"category": cat.to_dict()}), 201

@admin_bp.route("/admin/api/categories/<int:id>", methods=["GET"])
@jwt_required()
@admin_required
def get_category(id):
    cat = Category.query.get_or_404(id)
    return jsonify(cat.to_dict())

@admin_bp.route("/admin/api/categories/<int:id>", methods=["PATCH"])
@jwt_required()
@admin_required
def update_category(id):
    cat = Category.query.get_or_404(id)
    data = request.form
    if 'name' in data and data['name'] != cat.name:
        if Category.query.filter_by(name=data['name']).first():
            return jsonify({"error": "Name already taken"}), 400
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description'] or None
    db.session.commit()
    return jsonify({"category": cat.to_dict()})

@admin_bp.route("/admin/api/categories/<int:id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Category deleted"}), 200