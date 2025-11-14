from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from jinja2 import Environment

mail = Mail()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
app.jinja_env.filters['tojson'] = lambda v: __import__('json').dumps(v)