from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import Product
from flask_jwt_extended import jwt_required
import os

products_bp = Blueprint("products", __name__)

@products_bp.route("/", methods=["GET"])
def get_products():
    products = Product.query.all()
    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "image": p.image,
            "category_id": p.category_id
        })
    return jsonify(result)

@products_bp.route("/", methods=["POST"])
@jwt_required()
def add_product():
    data = request.form
    image_file = request.files.get("image")
    filename = None
    if image_file:
        filename = image_file.filename
        image_file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

    product = Product(
        name=data["name"],
        price=float(data["price"]),
        stock=int(data["stock"]),
        category_id=int(data["category_id"]),
        image=filename
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"id": product.id, "name": product.name})
