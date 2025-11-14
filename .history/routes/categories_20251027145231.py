from flask import Blueprint, request, jsonify
from extensions import db
from models import Category
from flask_jwt_extended import jwt_required

categories_bp = Blueprint("categories", __name__)

@categories_bp.route("/", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in categories])

@categories_bp.route("/", methods=["POST"])
@jwt_required()
def add_category():
    data = request.json
    if Category.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Category exists"}), 400
    category = Category(name=data["name"], description=data.get("description"))
    db.session.add(category)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name})
