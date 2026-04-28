# the DATABASE STRUCTURE for Finlytic
# Each class here becomes a table in the SQLite database (finlytic.db)
# SQLAlchemy maps Python objects to database rows automatically

from app import db, login_manager    # Import db and login_manager from __init__.py
from flask_login import UserMixin    # Adds required login helper methods to User
from datetime import datetime        # For recording when records are created


#  User Loader 
    # Flask-Login calls this function whenever it needs to load a logged-in user
    # It looks up the user by their ID stored in the session cookie
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#  USER TABLE
class User(db.Model, UserMixin):
    """
    Represents a registered user in the system.
    UserMixin adds: is_authenticated, is_active, is_anonymous, get_id()
    These are required by Flask-Login to manage sessions.
    """
    __tablename__ = 'users'  # Name of the table in the database

    # Primary key: unique ID auto-assigned to each new user
    id         = db.Column(db.Integer, primary_key=True)

    # User's display name (e.g., "You E Kry")
    username   = db.Column(db.String(80),  nullable=False)

    # Email must be unique: used as the login identifier
    email      = db.Column(db.String(120), unique=True, nullable=False)

    # Password stored as a HASH (Don't allow plain text for security)
    password   = db.Column(db.String(200), nullable=False)

    # Automatically set to current time when user registers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One-to-many relationship: one user can have many loan applications
    # backref='applicant' lets us do: application.applicant to get the user
    applications = db.relationship('LoanApplication', backref='applicant', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'


#  LOAN APPLICATION TABLE
class LoanApplication(db.Model):
    """
    Stores each loan prediction request made by a logged-in user.
    The 11 input fields here MUST match exactly what the ML model was trained on.
    This alignment is critical — the form, database, and model all use the same fields.
    """
    __tablename__ = 'loan_applications'

    # Primary key: nique ID for each application
    id                  = db.Column(db.Integer, primary_key=True)

    # Foreign key links this application to the user who submitted it
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #  11 ML Feature Fields 
    # These match the exact columns used to train the Logistic Regression model

    gender              = db.Column(db.String(10),  nullable=False)  # 'Male' or 'Female'
    married             = db.Column(db.String(5),   nullable=False)  # 'Yes' or 'No'
    dependents          = db.Column(db.String(5),   nullable=False)  # '0', '1', '2', '3+'
    education           = db.Column(db.String(20),  nullable=False)  # 'Graduate' or 'Not Graduate'
    self_employed       = db.Column(db.String(5),   nullable=False)  # 'Yes' or 'No'
    applicant_income    = db.Column(db.Float,       nullable=False)  # Monthly income in $
    coapplicant_income  = db.Column(db.Float,       nullable=False)  # Co-applicant monthly income
    loan_amount         = db.Column(db.Float,       nullable=False)  # Requested loan amount in $
    loan_amount_term    = db.Column(db.Float,       nullable=False)  # Loan duration in months
    credit_history      = db.Column(db.Float,       nullable=False)  # 1.0 = Good, 0.0 = Bad
    property_area       = db.Column(db.String(10),  nullable=False)  # 'Urban', 'Semiurban', 'Rural'

    #  ML Model Output 
    prediction          = db.Column(db.String(10),  nullable=False)  # 'Approved' or 'Rejected'
    probability         = db.Column(db.Float,       nullable=False)  # Confidence score (0-100%)

    # Timestamp of when the prediction was made
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LoanApplication {self.id} — {self.prediction}>'