from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from jinja2 import Environment

mail = Mail()

CORS(app)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
