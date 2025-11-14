from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Order, OrderItem, Product

invoices_bp = Blueprint("invoices", __name__)

@invoices_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    cart_items = session.get("cart", {})
    if not cart_items:
        return jsonify({"error": "Cart empty"}), 400

    order = Order(user_id=user_id)
    db.session.add(order)
    db.session.commit()

    total_price = 0
    for pid, qty in cart_items.items():
        product = Product.query.get(int(pid))
        if product:
            item_price = float(product.price)
            total_price += item_price * qty
            order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=qty, price=item_price)
            db.session.add(order_item)

    order.total_price = total_price
    db.session.commit()
    session.pop("cart", None)
    return jsonify({"message": "Order placed", "order_id": order.id, "total": total_price})
