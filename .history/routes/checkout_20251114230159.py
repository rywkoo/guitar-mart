# routes/checkout.py  (updated email section)

from flask_mail import Message  # ADD THIS AT TOP

# ...

@checkout_bp.route("/create_invoice", methods=["POST"])
@jwt_required()
def create_invoice():
    from flask import request, current_app
    import json

    # ... [your existing code until after db.commit()] ...

    # Send email using Flask-Mail
    try:
        msg = Message(
            subject=f"Your Invoice {invoice_number}",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        msg.body = f"""Hello {user.username},

Thank you for your order!

Invoice Number: {invoice_number}
Total Amount: ${total_amount:.2f}

View your invoice at: {request.url_root}invoices/{invoice_number}

- Mini Mart
"""

        mail.send(msg)
        print(f"Invoice email sent to {user.email}")
    except Exception as e:
        print("Email send failed:", str(e))
        # Don't fail the checkout just because email failed
        # But log it for debugging
        pass

    return jsonify({"success": True, "invoice_number": invoice_number})