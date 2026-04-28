import os  #read environment variables and build file paths

class Config:
    """
    Configuration class for the Finlytic Flask application.
    All app settings are stored here so they can be easily changed in one place.
    """

    # SECRET_KEY is used by Flask to:
    # 1. Sign session cookies (keeps users logged in securely)
    # 2. Protect forms from CSRF (Cross-Site Request Forgery) attacks
    # It first checks for an environment variable, then falls back to our default key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'finlytic-secret-key-2025'

    # SQLALCHEMY_DATABASE_URI tells Flask-SQLAlchemy WHERE to store the database
    # Using SQLite: a lightweight file-based database (finlytic.db)
    # os.path.abspath ensures the path works no matter where the app is run from
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'finlytic.db')

    # Disables a Flask-SQLAlchemy feature that tracks object changes
    # Don't need it and it uses extra memory, so we turn it off
    SQLALCHEMY_TRACK_MODIFICATIONS = False