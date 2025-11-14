# routes/admin.py
from flask import Blueprint, render_template, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Product, Category, Invoice
from datetime import datetime, timedelta
import os
from functools import wraps

admin_bp = Blueprint("admin", __name__, template_folder='templates')


# -------------------
# DECORATORS
# -------------------
def admin_required(fn):
    """Ensure JWT has role: admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims or claims.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


# -------------------
# HELPERS
# -------------------
def save_image(file):
    """Save uploaded image securely and return filename."""
    if not file or not file.filename:
        return None
    filename = secure_filename(file.filename)
    if not filename:
        return None
    path = os.path.join("static", "images", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
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


@admin_bp.route("/admin/categories")
@jwt_required()
@admin_required
def categories():
    cats = Category.query.all()
    return render_template("admin/category.html", categories=cats)


# -------------------
# PRODUCTS API
# -------------------
@admin_bp.route("/admin/api/products", methods=["GET"]strict_slashes=False)
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

    try:
        price = float(price)
        stock = int(stock)
        category_id = int(category_id) if category_id else None
    except ValueError:
        return jsonify({"error": "Invalid price, stock, or category_id"}), 400

    image_filename = save_image(image_file)

    product = Product(
        name=name,
        price=price,
        stock=stock,
        category_id=category_id,
        image=image_filename
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({
        "message": "Product added",
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "category_id": product.category_id,
            "category_name": product.category.name if product.category else None,
            "image": product.image
        }
    }), 201


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

    if name is not None:
        p.name = name
    if price is not None:
        try:
            p.price = float(price)
        except ValueError:
            return jsonify({"error": "Invalid price"}), 400
    if stock is not None:
        try:
            p.stock = int(stock)
        except ValueError:
            return jsonify({"error": "Invalid stock"}), 400
    if category_id is not None:
        p.category_id = int(category_id) if category_id else None
    if image_file and image_file.filename:
        p.image = save_image(image_file)

    db.session.commit()

    return jsonify({
        "message": "Product updated",
        "product": {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "image": p.image
        }
    }), 200


@admin_bp.route("/admin/api/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_product(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": f"Product '{p.name}' deleted"}), 200


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
    return jsonify({"message": f"User '{u.username}' deleted"}), 200


# -------------------
# CATEGORIES API
# -------------------
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
    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({"error": "Category already exists"}), 400

    cat = Category(name=name, description=description or None)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"category": cat.to_dict()}), 201


@admin_bp.route("/admin/api/categories/<int:id>", methods=["GET"])
@jwt_required()
@admin_required
def get_category(id):
    cat = Category.query.get_or_404(id)
    return jsonify(cat.to_dict()), 200


@admin_bp.route("/admin/api/categories/<int:id>", methods=["PATCH"])
@jwt_required()
@admin_required
def update_category(id):
    cat = Category.query.get_or_404(id)
    data = request.form

    name = data.get("name")
    description = data.get("description")

    if name and name != cat.name:
        if Category.query.filter_by(name=name).first():
            return jsonify({"error": "Name already taken"}), 400
        cat.name = name
    if description is not None:
        cat.description = description or None

    db.session.commit()
    return jsonify({"category": cat.to_dict()}), 200


@admin_bp.route("/admin/api/categories/<int:id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Category deleted"}), 200


# -------------------
# PURCHASE REPORTS
# -------------------
@admin_bp.route("/admin/api/reports/purchases", methods=["GET"])
@jwt_required()
@admin_required
def purchase_report():
    report_type = request.args.get("type", "daily")
    username_filter = request.args.get("username")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    now = datetime.utcnow()
    query = Invoice.query

    if username_filter:
        query = query.filter(Invoice.username.ilike(f"%{username_filter}%"))

    labels = []
    totals = []

    def daily_total(start, end):
        return sum(inv.total_amount for inv in query.filter(
            Invoice.created_at >= start,
            Invoice.created_at < end
        ).all())

    if report_type == "daily":
        today_start = datetime(now.year, now.month, now.day)
        total = daily_total(today_start, today_start + timedelta(days=1))
        labels = ["Today"]
        totals = [total]

    elif report_type == "weekly":
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            start = datetime(day.year, day.month, day.day)
            end = start + timedelta(days=1)
            labels.append(start.strftime("%b %d"))
            totals.append(daily_total(start, end))

    elif report_type == "monthly":
        for i in range(29, -1, -1):
            day = now - timedelta(days=i)
            start = datetime(day.year, day.month, day.day)
            end = start + timedelta(days=1)
            labels.append(start.strftime("%b %d"))
            totals.append(daily_total(start, end))

    elif report_type == "custom" and start_date and end_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            current = datetime(start_dt.year, start_dt.month, start_dt.day)
            while current <= end_dt:
                start = current
                end = start + timedelta(days=1)
                labels.append(start.strftime("%b %d"))
                totals.append(daily_total(start, end))
                current += timedelta(days=1)
        except Exception as e:
            return jsonify({"error": "Invalid date format"}), 400

    return jsonify({"labels": labels, "totals": totals})


# -------------------
# INVOICES API
# -------------------
@admin_bp.route("/admin/api/invoices", methods=["GET"])
@jwt_required()
@admin_required
def get_all_invoices():
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