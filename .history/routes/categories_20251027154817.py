from flask import Blueprint, request, jsonify
from extensions import db
from models import Category
from flask_jwt_extended import jwt_required, get_jwt

categories_bp = Blueprint("categories", __name__)

# Get all categories
@categories_bp.route("/", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    result = [{"id": c.id, "name": c.name, "description": c.description} for c in categories]
    return jsonify(result)

# Create a new category (admin only)
@categories_bp.route("/", methods=["POST"])
@jwt_required()
def add_category():
    claims = get_jwt()
    if claims.get("role", "user") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.json
    if Category.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Category already exists"}), 400

    category = Category(name=data["name"], description=data.get("description", ""))
    db.session.add(category)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name}), 201

# Update category (admin only)
@categories_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_category(id):
    claims = get_jwt()
    if claims.get("role", "user") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    category = Category.query.get_or_404(id)
    data = request.json
    category.name = data.get("name", category.name)
    category.description = data.get("description", category.description)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name})

# Delete category (admin only)
@categories_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_category(id):
    claims = get_jwt()
    if claims.get("role", "user") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted"})
