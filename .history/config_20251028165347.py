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
    JWT_COOKIE_SECURE = False                # allow HTTP (localhost)
    JWT_ACCESS_COOKIE_PATH = "/"             # cookie valid for whole site
    JWT_REFRESH_COOKIE_PATH = "/token/refresh"
    # Mail settings — no commas!
    MAIL_SERVER = 'smtp.gmail.com'   # e.g., Gmail SMTP
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'theareachmiku@gmail.com'
    MAIL_PASSWORD = 'qwtfywcuwcybzydd'  # Use Gmail App Password
    MAIL_DEFAULT_SENDER = 'mini-mart@mail.su79.setec'
