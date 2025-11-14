from flask import Blueprint, request, jsonify, session
from models import Product

cart_bp = Blueprint("cart", __name__)

@cart_bp.route("/", methods=["GET"])
def get_cart():
    cart_items = session.get("cart", {})
    products = []
    for pid, qty in cart_items.items():
        product = Product.query.get(int(pid))
        if product:
            products.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "quantity": qty,
                "subtotal": float(product.price) * qty
            })
    return jsonify(products)

@cart_bp.route("/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session["cart"] = cart
    return jsonify({"message": "Added to cart"})
