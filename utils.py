# utils.py
from flask_mail import Message
from extensions import mail
from flask import current_app

def send_email(to_email, subject, body):
    msg = Message(subject=subject, recipients=[to_email], body=body)
    mail.send(msg)
