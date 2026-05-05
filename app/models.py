# ============================================================
# FILE: models.py
# PURPOSE: Database Structure for Finlytic
# DESCRIPTION: Defines the database tables using SQLAlchemy ORM.
#              Each class here becomes a table in the SQLite database (finlytic.db)
#              SQLAlchemy maps Python objects to database rows automatically.
#              This allows us to work with database records as Python objects.
# ============================================================

# ============================================================
# IMPORTS
# ============================================================
from app import db, login_manager    # Import db and login_manager from __init__.py
from flask_login import UserMixin    # Adds required login helper methods to User class
from datetime import datetime        # For recording when records are created (timestamps)


# ============================================================
# USER LOADER FUNCTION (Flask-Login Requirement)
# ============================================================
# Flask-Login calls this function whenever it needs to load a logged-in user.
# It looks up the user by their ID stored in the session cookie.
# This function is required for Flask-Login to work properly.
@login_manager.user_loader
def load_user(user_id):
    """Retrieve a user from the database by their ID."""
    # Query the User table for a record with the given ID
    # Convert user_id from string to integer (session stores IDs as strings)
    return User.query.get(int(user_id))


# ============================================================
# TABLE 1: USER TABLE
# ============================================================
class User(db.Model, UserMixin):
    """
    Represents a registered user in the system.
    
    UserMixin adds required Flask-Login methods:
    - is_authenticated: Returns True (user is logged in)
    - is_active: Returns True (account is active)
    - is_anonymous: Returns False (this is a real user, not anonymous)
    - get_id(): Returns the user's unique ID as a string
    
    Without UserMixin, Flask-Login would not work properly.
    """
    __tablename__ = 'users'  # Name of the table in the database (optional but good practice)

    # ============================================================
    # COLUMN DEFINITIONS
    # ============================================================
    
    # PRIMARY KEY: Unique ID auto-assigned to each new user
    # Integer values automatically increment (1, 2, 3, ...)
    id = db.Column(db.Integer, primary_key=True)

    # User's display name (e.g., "You E Kry")
    # String(80): Maximum 80 characters
    # nullable=False: This field cannot be empty
    username = db.Column(db.String(80), nullable=False)

    # Email address (used as login identifier)
    # unique=True: No two users can have the same email
    # String(120): Maximum 120 characters
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Password hash (never store plain text passwords in production!)
    # In a real app, this would store a hashed version using bcrypt or werkzeug
    # String(200): Enough space for a hashed password
    password = db.Column(db.String(200), nullable=False)

    # Automatically set to current UTC time when user registers
    # default=datetime.utcnow: Uses the time the record is created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    # One-to-many relationship: one user can have many loan applications
    # 'LoanApplication' refers to the other model class
    # backref='applicant': Creates a virtual column on LoanApplication
    #   So we can do: application.applicant to get the user
    # lazy=True: Loads applications only when accessed (performance optimization)
    applications = db.relationship('LoanApplication', backref='applicant', lazy=True)

    # ============================================================
    # REPRESENTATION METHOD (for debugging)
    # ============================================================
    def __repr__(self):
        """String representation of the User object (used in console/debugging)."""
        return f'<User {self.email}>'


# ============================================================
# TABLE 2: LOAN APPLICATION TABLE
# ============================================================
class LoanApplication(db.Model):
    """
    Stores each loan prediction request made by a logged-in user.
    
    CRITICAL: The 11 input fields here MUST match exactly what the ML model was trained on.
    The form, database, and model all use the same fields in the same order.
    This alignment is essential for the model to make accurate predictions.
    """
    __tablename__ = 'loan_applications'

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    # Unique ID for each application (auto-increments)
    id = db.Column(db.Integer, primary_key=True)

    # ============================================================
    # FOREIGN KEY (Links to User table)
    # ============================================================
    # Foreign key connects this application to the user who submitted it
    # db.ForeignKey('users.id'): References the id column in users table
    # nullable=False: Every application must belong to a user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # ============================================================
    # THE 11 ML FEATURE FIELDS (Input Features)
    # ============================================================
    # These match the exact columns used to train the model
    # The model expects these features in this exact order
    
    # Gender: 'Male' or 'Female' (categorical)
    gender = db.Column(db.String(10), nullable=False)
    
    # Married status: 'Yes' or 'No' (categorical)
    married = db.Column(db.String(5), nullable=False)
    
    # Number of dependents: '0', '1', '2', '3+' (categorical)
    dependents = db.Column(db.String(5), nullable=False)
    
    # Education level: 'Graduate' or 'Not Graduate' (categorical)
    education = db.Column(db.String(20), nullable=False)
    
    # Self-employment status: 'Yes' or 'No' (categorical)
    self_employed = db.Column(db.String(5), nullable=False)
    
    # Applicant's monthly income in dollars (numeric)
    applicant_income = db.Column(db.Float, nullable=False)
    
    # Co-applicant's monthly income in dollars (numeric, can be 0)
    coapplicant_income = db.Column(db.Float, nullable=False)
    
    # Requested loan amount in dollars (numeric)
    loan_amount = db.Column(db.Float, nullable=False)
    
    # Loan duration in months (numeric: 360, 180, 120, 84, 60, 36, 12)
    loan_amount_term = db.Column(db.Float, nullable=False)
    
    # Credit history: 1.0 = Good credit, 0.0 = Bad/No credit (numeric)
    credit_history = db.Column(db.Float, nullable=False)
    
    # Property area: 'Urban', 'Semiurban', 'Rural' (categorical)
    property_area = db.Column(db.String(10), nullable=False)

    # ============================================================
    # MODEL OUTPUT FIELDS (What the ML model predicted)
    # ============================================================
    
    # Model's decision: 'Approved' or 'Rejected'
    prediction = db.Column(db.String(10), nullable=False)
    
    # Model's confidence score: 0-100% (how sure the model is)
    probability = db.Column(db.Float, nullable=False)

    # ============================================================
    # TIMESTAMP
    # ============================================================
    # When this prediction was made (UTC time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ============================================================
    # REPRESENTATION METHOD (for debugging)
    # ============================================================
    def __repr__(self):
        """String representation of the LoanApplication object."""
        return f'<LoanApplication {self.id} — {self.prediction}>'


# ============================================================
# HOW THE DATABASE WORKS:
# ============================================================
#
# 1. When create_app() runs, db.create_all() creates both tables
# 2. New users are added to 'users' table via registration form
# 3. Loan predictions are saved to 'loan_applications' table
# 4. Each application has a user_id linking back to the user who submitted it
# 
# RELATIONSHIPS:
# - One User → Many LoanApplications (one-to-many)
# - To get a user's applications: user.applications
# - To get the user for an application: application.applicant
#
# EXAMPLE QUERIES:
# ---------------
# # Get all users
# users = User.query.all()
#
# # Find user by email
# user = User.query.filter_by(email='john@example.com').first()
#
# # Get all applications for a user
# apps = user.applications
#
# # Get all approved applications
# approved = LoanApplication.query.filter_by(prediction='Approved').all()
#
# # Get applications with high confidence
# confident = LoanApplication.query.filter(LoanApplication.probability > 80).all()
# ============================================================