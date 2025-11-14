import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = "sqlite:///mini_mart.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "supersecretjwtkey")
    UPLOAD_FOLDER = "static/images"

    # JWT cookie settings
    JWT_TOKEN_LOCATION = ["cookies"]        # read JWT from cookies
    JWT_COOKIE_CSRF_PROTECT = False         # disable CSRF for simplicity
