# ============================================================
# FILE: forms.py
# PURPOSE: Define all web forms used in the Finlytic application
# DESCRIPTION: Contains WTForms classes for user registration, login,
#              and loan prediction. These forms handle:
#              - Data validation (ensuring required fields are filled)
#              - Input sanitization (preventing malicious data)
#              - CSRF protection (security against cross-site request forgery)
# ============================================================

# ============================================================
# IMPORTS
# ============================================================
from flask_wtf import FlaskForm          # Base class for all Flask forms (adds CSRF protection)
from wtforms import StringField, PasswordField, SelectField, FloatField
                                         # Field types:
                                         # - StringField: Text input (short text)
                                         # - PasswordField: Text input with hidden characters (••••••)
                                         # - SelectField: Dropdown menu
                                         # - FloatField: Number input (decimal values)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange
                                         # Validation rules:
                                         # - DataRequired: Field cannot be empty
                                         # - Email: Must be valid email format
                                         # - EqualTo: Must match another field (password confirmation)
                                         # - Length: Minimum/maximum characters
                                         # - NumberRange: Minimum/maximum numeric value


# ============================================================
# FORM 1: USER REGISTRATION
# ============================================================
# Used when a new user signs up for an account
class RegisterForm(FlaskForm):
    """Registration form for new users - creates a new account"""
    
    # Username field - the user's full name or display name
    username = StringField('Full Name',
                  validators=[DataRequired(), Length(min=2, max=80)])
                  # DataRequired(): Cannot be empty
                  # Length(min=2, max=80): Between 2 and 80 characters
    
    # Email field - used for login and account recovery
    email = StringField('Email',
               validators=[DataRequired(), Email()])
               # Email(): Validates that input matches email format (user@example.com)
    
    # Password field - user's secret password (input is masked)
    password = PasswordField('Password',
                    validators=[DataRequired(), Length(min=6)])
                    # Length(min=6): Password must be at least 6 characters
    
    # Confirm password field - user must type password again to verify
    confirm_password = PasswordField('Confirm Password',
                           validators=[DataRequired(),
                                       EqualTo('password',
                                       message='Passwords must match')])
                           # EqualTo('password'): Must match the password field value
                           # Custom error message if mismatch


# ============================================================
# FORM 2: USER LOGIN
# ============================================================
# Used when an existing user signs in
class LoginForm(FlaskForm):
    """Login form for existing users - authenticates credentials"""
    
    # Email field - user's registered email address
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    # Password field - user's password (matched against database)
    password = PasswordField('Password', validators=[DataRequired()])


# ============================================================
# FORM 3: LOAN PREDICTION (APPLICATION)
# ============================================================
# Used when a user applies for a loan - this is the CORE form of the app
# All data from this form is sent to the machine learning model
class LoanForm(FlaskForm):
    """Loan application form - collects all data needed for AI prediction"""
    
    # ============================================================
    # SECTION A: PERSONAL INFORMATION
    # ============================================================
    
    # Gender dropdown (Male/Female)
    gender = SelectField('Gender', validators=[DataRequired()], choices=[
        ('', 'Select gender'),   # Empty placeholder - user must select
        ('Male', 'Male'),
        ('Female', 'Female')
    ])
    
    # Marital status dropdown
    married = SelectField('Married', validators=[DataRequired()], choices=[
        ('', 'Select status'),
        ('Yes', 'Yes'),
        ('No', 'No')
    ])
    
    # Number of dependents (children/others financially dependent)
    dependents = SelectField('Dependents', validators=[DataRequired()], choices=[
        ('', 'Select dependents'),
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3+', '3+')      # '3+' is stored as string, converted later
    ])
    
    # Education level - important for loan risk assessment
    education = SelectField('Education', choices=[
        ('', 'Select education'),  
        ('High School', 'High School'),
        ('Bachelor', 'Bachelor'), 
        ('Master', 'Master'),
        ('PhD', 'PhD')
    ], validators=[DataRequired()])
    
    # Self-employment status (business owner vs salaried employee)
    self_employed = SelectField('Self Employed', validators=[DataRequired()], choices=[
        ('', 'Select status'),
        ('Yes', 'Yes'),
        ('No', 'No')
    ])
    
    # ============================================================
    # SECTION B: FINANCIAL INFORMATION
    # ============================================================
    
    # Applicant's monthly income (primary earner)
    applicant_income = FloatField('Applicant Income',
                           validators=[DataRequired(), NumberRange(min=0)])
                           # NumberRange(min=0): Cannot be negative
    
    # Co-applicant's monthly income (spouse/partner)
    coapplicant_income = FloatField('Coapplicant Income',
                             validators=[DataRequired(), NumberRange(min=0)])
                             # Can be 0 if applying alone
    
    # ============================================================
    # SECTION C: LOAN DETAILS
    # ============================================================
    
    # Total loan amount requested
    loan_amount = FloatField('Loan Amount',
                      validators=[DataRequired(), NumberRange(min=1)])
                      # NumberRange(min=1): Must be at least $1
    
    # Loan term (repayment period in months)
    # Common terms: 30 years (360 months), 15 years (180 months), etc.
    loan_amount_term = SelectField('Loan Term', validators=[DataRequired()], choices=[
        ('', 'Select term'),
        ('360', '360 months (30 years)'),
        ('180', '180 months (15 years)'),
        ('120', '120 months (10 years)'),
        ('84',  '84 months (7 years)'),
        ('60',  '60 months (5 years)'),
        ('36',  '36 months (3 years)'),
        ('12',  '12 months (1 year)'),
    ])
    
    # Credit history status (Good = 1, Bad/No credit = 0)
    # This is often the most important factor in loan approval
    credit_history = SelectField('Credit History', validators=[DataRequired()], choices=[
        ('', 'Select history'),
        ('1', 'Good (1)'),    # Has good credit history
        ('0', 'Bad (0)')      # Has poor or no credit history
    ])
    
    # Property area type - affects property value and loan risk
    property_area = SelectField('Property Area', validators=[DataRequired()], choices=[
        ('', 'Select area'),
        ('Urban', 'Urban'),         # City area (high property value)
        ('Semiurban', 'Semiurban'), # Suburb area (medium property value)
        ('Rural', 'Rural')          # Country area (lower property value)
    ])


# ============================================================
# HOW THE FORMS ARE USED IN ROUTES.PY:
# ============================================================
# 
# In routes.py, you'll see code like this:
#
# from app.forms import LoanForm, RegisterForm, LoginForm
#
# @main_bp.route('/predict', methods=['GET', 'POST'])
# def predict():
#     form = LoanForm()                    # Create form instance
#     if form.validate_on_submit():        # Check if form is valid (POST request)
#         # Access data: form.gender.data, form.applicant_income.data, etc.
#         # Send data to ML model for prediction
#         # Redirect to result page
#     return render_template('predict.html', form=form)
#
# ============================================================