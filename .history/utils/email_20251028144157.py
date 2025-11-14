# utils/email.py
from flask_mail import Message
from extensions import mail
from flask import current_app

def send_email(to, subject, body):
    msg = Message(subject, recipients=[to], body=body, sender=current_app.config['MAIL_USERNAME'])
    mail.send(msg)
