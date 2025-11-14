# products.py
from flask import Blueprint, request, jsonify, current_app, url_for
from extensions import db
from models import Product
from flask_jwt_extended import jwt_required, get_jwt
import os

products_bp = Blueprint("products", __name__, url_prefix="/api/products")

@products_bp.route("/", methods=["GET"])
def get_products():
    products = Product.query.all()
    result = []
    for p in products:
        image_url = None
        if p.image:
            # Build full URL: /static/images/filename.jpg
            image_url = url_for('static', filename=f'images/{p.image}', _external=True)
        
        result.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "image_url": image_url,        # ← Full URL
            "category_id": p.category_id
        })
    return jsonify(result)


@products_bp.route("/", methods=["POST"])
@jwt_required()
def add_product():
    claims = get_jwt()
    role = claims.get("role", "user")
    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.form
    image_file = request.files.get("image")
    filename = None

    if image_file and image_file.filename:
        filename = image_file.filename
        upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        image_file.save(upload_path)

    product = Product(
        name=data["name"],
        price=float(data["price"]),
        stock=int(data["stock"]),
        category_id=int(data["category_id"]),
        image=filename  # ← store only filename
    )
    db.session.add(product)
    db.session.commit()

    # Return full image URL in response
    image_url = url_for('static', filename=f'images/{filename}', _external=True) if filename else None

    return jsonify({
        "id": product.id,
        "name": product.name,
        "image_url": image_url
    }), 201