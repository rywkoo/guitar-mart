from flask_mail import Message
from flask import Blueprint, request, jsonify
from extensions import mail

@reset_bp.route("/request", methods=["POST"])
def request_reset():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Create short-lived reset token
    reset_token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=15))

    # Send email with token
    try:
        msg = Message(
            subject="Your Mini Mart Password Reset Token",
            recipients=[user.email],
            body=f"Hello {user.username},\n\n"
                 f"Here is your password reset token. It is valid for 15 minutes:\n\n"
                 f"{reset_token}\n\n"
                 "If you did not request a password reset, please ignore this email."
        )
        mail.send(msg)
    except Exception as e:
        return jsonify({"msg": f"Failed to send email: {str(e)}"}), 500

    # Return success message without showing token in browser
    return jsonify({"msg": "Reset token has been sent to your email!"}), 200
