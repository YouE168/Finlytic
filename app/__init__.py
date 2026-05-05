# ============================================================
# FILE: app/__init__.py
# PURPOSE: Application Factory - Creates and configures the Flask app
# DESCRIPTION: This is the heart of the Flask application. It initializes
#              all extensions (database, login manager), registers blueprints,
#              and creates database tables. Using a factory pattern makes the
#              app easier to test and scale.
# ============================================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy   # Database ORM (Object Relational Mapper)
                                          # ORM lets us work with database tables as Python objects
from flask_login import LoginManager      # Handles user authentication sessions
                                          # Manages login, logout, and "remember me" functionality
from config import Config                 # Custom settings from config.py (SECRET_KEY, database URI, etc.)

# ============================================================
# CREATE EXTENSION INSTANCES (not yet connected to any app)
# ============================================================
# These are created here at module level so other files (models.py, routes.py)
# can import them without causing circular imports.
db = SQLAlchemy()        # Manages all database operations (queries, inserts, updates)
login_manager = LoginManager()  # Manages user sessions and authentication state

# ============================================================
# FLASK-LOGIN CONFIGURATION
# ============================================================
# Tell Flask-Login which route to redirect to when a user tries to access 
# a page that requires login (like Dashboard) without being logged in
login_manager.login_view = 'auth.login'  # Points to the 'login' function in the 'auth' blueprint

# Set the flash message category when redirected to login
# 'danger' makes the alert show in red (error styling)
login_manager.login_message_category = 'danger'


def create_app():
    """
    Application Factory Function.
    Creates and returns a fully configured Flask app.
    
    WHY USE A FACTORY FUNCTION?
    - Allows multiple app instances (useful for testing)
    - Makes configuration easier to manage
    - Keeps code organized and modular
    - Avoids global state issues
    """
    
    # ============================================================
    # CREATE FLASK APPLICATION INSTANCE
    # ============================================================
    # __name__ tells Flask where to look for templates and static files
    # This resolves to the 'app' directory
    app = Flask(__name__)
    
    # ============================================================
    # LOAD CONFIGURATION SETTINGS
    # ============================================================
    # Load all configuration settings from our Config class (in config.py)
    # This includes: SECRET_KEY, SQLALCHEMY_DATABASE_URI, etc.
    app.config.from_object(Config)
    
    # ============================================================
    # INITIALIZE EXTENSIONS WITH THE APP
    # ============================================================
    # This connects SQLAlchemy and LoginManager to our specific Flask app
    db.init_app(app)           # Database connection: creates session, handles queries
    login_manager.init_app(app)  # Authentication system: manages user sessions
    
    # ============================================================
    # REGISTER BLUEPRINTS
    # ============================================================
    # Blueprints are like "mini-apps" that group related routes together
    # They allow us to organize code by feature rather than by file type
    
    # Import blueprints from routes.py
    from app.routes import main, auth
    
    # Register blueprints with the main app
    # 'main' blueprint handles: Home, Predict, Dashboard (main pages)
    # 'auth' blueprint handles: Register, Login, Logout (authentication pages)
    app.register_blueprint(main)
    app.register_blueprint(auth)
    
    # ============================================================
    # CREATE DATABASE TABLES
    # ============================================================
    # app_context() makes the app available to background operations
    # Without this, Flask wouldn't know which app to use for database operations
    with app.app_context():
        # db.create_all() reads our models (User in models.py) and creates tables if they don't exist
        # This is safe to run multiple times — it won't overwrite existing data
        # Tables are created in the database file specified in config.py (finlytic.db)
        db.create_all()
    
    # ============================================================
    # RETURN THE FULLY CONFIGURED APP
    # ============================================================
    # The returned app is then used by run.py to start the web server
    return app


# ============================================================
# HOW THE APPLICATION STARTS:
# ============================================================
# 1. run.py calls create_app()
# 2. Flask app instance is created
# 3. Config settings are loaded
# 4. Database and LoginManager are connected
# 5. Blueprints are registered (routes become available)
# 6. Database tables are created
# 7. App is returned to run.py and starts the web server
# 8. User can now access http://127.0.0.1:5000
# ============================================================