# __init__.py is application factory
# It creates and configures the Flask app, connects all the pieces together

from flask import Flask
from flask_sqlalchemy import SQLAlchemy   # Database ORM (Object Relational Mapper)
from flask_login import LoginManager      # Handles user authentication sessions
from config import Config                 # custom settings from config.py

# Create extension instances but not yet tied to any app
# These are created here at module level so other files can import them
db = SQLAlchemy()    # Manages all database operations
login_manager = LoginManager()

# Tell Flask-Login which route to redirect to when a user tries to access a page that requires login
login_manager.login_view = 'auth.login'

# Set the flash message category when redirected to login
# 'danger' makes the alert show in red 
login_manager.login_message_category = 'danger'


def create_app():
    """
    Application Factory Function.
    Creates and returns a fully configured Flask app.
    Using a factory function makes the app easier to test and scale.
    """

    # Create the Flask application instance
    # __name__ tells Flask where to look for templates and static files
    app = Flask(__name__)

    # Load all configuration settings from our Config class
    app.config.from_object(Config)

    # Initialize extensions w/ the app 
        # This connects SQLAlchemy and LoginManager to our specific Flask app
    db.init_app(app)
    login_manager.init_app(app)

    #  Register Blueprints 
        # Blueprints are like "mini-apps" that group related routes together
        # 'main' blueprint handles: home, predict, dashboard
        # 'auth' blueprint handles: register, login, logout
    from app.routes import main, auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    # Create database tables
        # app_context() makes the app available to background operations
        # db.create_all() reads our models and creates tables if they don't exist yet
        # This is safe to run multiple times — it won't overwrite existing data
    with app.app_context():
        db.create_all()

    return app  # Return the fully configured app to run.py