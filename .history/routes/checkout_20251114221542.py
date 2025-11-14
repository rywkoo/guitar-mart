from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Invoice, InvoiceItem, Product, db
from datetime import datetime
import smtplib
from email.message import EmailMessage

checkout_bp = Blueprint("checkout", __name__)

@checkout_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    """
    Checkout the user's cart:
    - Identify user via JWT
    - Create Invoice & InvoiceItems
    - Send email notification with invoice details
    """
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    if not user:
        return jsonify({"success": False, "msg": "User not found"}), 404

    data = request.get_json()
    cart = data.get("cart", [])

    if not cart:
        return jsonify({"success": False, "msg": "Cart is empty"}), 400

    # Calculate total
    total_amount = 0
    for item in cart:
        product = Product.query.get(item.get("id"))
        if not product:
            return jsonify({"success": False, "msg": f"Product {item.get('id')} not found"}), 404
        total_amount += product.price * item.get("quantity", 1)

    # Create Invoice
    invoice_number = Invoice.generate_invoice_number()
    invoice = Invoice(username=user.username, invoice_number=invoice_number, total_amount=total_amount)
    db.session.add(invoice)
    db.session.commit()  # commit to get invoice.id

    # Create Invoice Items
    for item in cart:
        product = Product.query.get(item.get("id"))
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            quantity=item.get("quantity", 1),
            price=product.price
        )
        db.session.add(invoice_item)

    db.session.commit()

    # Send invoice email
    try:
        items_list = "\n".join([f"{Product.query.get(item['id']).name} x{item['quantity']} - ${Product.query.get(item['id']).price*item['quantity']:.2f}" for item in cart])
        msg = EmailMessage()
        msg['Subject'] = f"Mini Mart Invoice #{invoice_number}"
        msg['From'] = "yourstore@example.com"
        msg['To'] = user.email
        msg.set_content(f"""
Hi {user.username},

Thank you for your order! Here is your invoice:

Invoice Number: {invoice_number}
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
Items:
{items_list}

Total: ${total_amount:.2f}

Thank you for shopping with Mini Mart!

Best regards,
Mini Mart Team
""")
        # Example using Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("yourstore@example.com", "your-email-password")
            smtp.send_message(msg)
    except Exception as e:
        print("Email sending failed:", e)

    return jsonify({"success": True, "invoice_number": invoice_number})
