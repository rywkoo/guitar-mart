# utils/email_utils.py
from flask_mail import Message
from extensions import mail
from flask import current_app

def send_email(to, subject, body):
    msg = Message(
        subject=subject,
        recipients=[to],
        body=body,
        sender=current_app.config.get("MAIL_USERNAME")
    )
    mail.send(msg)
