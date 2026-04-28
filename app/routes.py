# routes.py handles all URL routing and business logic for Finlytic
# A "route" maps a URL (like /predict) to a Python function that handles it
# We use Flask Blueprints to organize routes into two groups: main and auth

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, LoanApplication
from app.forms import RegisterForm, LoginForm, LoanForm
import joblib       # Used to load the saved ML model (.pkl file)
import numpy as np  # Used to create the feature array for prediction
import os
import json

#  Create Blueprints 
# Blueprints group related routes together like "mini Flask apps"
main = Blueprint('main', __name__)   # Public pages: home, predict, dashboard
auth = Blueprint('auth', __name__)   # Auth pages: register, login, logout

#  Load the ML Model and Scaler at Startup 
# We load the model ONCE when the app starts (not on every request)
# This makes predictions much faster since loading is slow
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'scaler.pkl')
model = None
scaler = None

# Load the model
if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"⚠️ Model not loaded: {e}")

# Load the scaler if it exists (for Logistic Regression)
if os.path.exists(SCALER_PATH) and os.path.getsize(SCALER_PATH) > 0:
    try:
        scaler = joblib.load(SCALER_PATH)
        print("✅ Scaler loaded successfully")
    except Exception as e:
        print(f"⚠️ Scaler not loaded: {e}")


# ════════════════════════════════
#  MAIN ROUTES
# ════════════════════════════════

@main.route('/')
def index():
    """
    Home page route.
    Just renders the landing page — no data processing needed.
    """
    return render_template('index.html')


@main.route('/predict', methods=['GET', 'POST'])
def predict():
    """
    Loan Prediction route — the core feature of Finlytic.

    GET request:  User visits /predict → show the empty loan form
    POST request: User submits the form → validate → predict → show result
    """
    form = LoanForm()  # Create a new form instance

    # form.validate_on_submit() returns True only when:
    # 1. The request is POST (form was submitted)
    # 2. All validators pass (no empty fields, valid numbers, etc.)
    if form.validate_on_submit():

        #  Step 1: Encode form inputs to match ML model training format 
        # The model was trained on numbers, not strings
        # So we convert text values → integers/floats exactly as done during training

        gender_val     = 1 if form.gender.data == 'Male' else 0         # Male=1, Female=0
        married_val    = 1 if form.married.data == 'Yes' else 0         # Yes=1, No=0
        dependents_val = 3 if form.dependents.data == '3+' else int(form.dependents.data)
        
        # IMPORTANT: Map education from form options to numeric values
        # Your form shows: High School, Bachelor, Master, PhD
        # Map them to numbers that match your training
        education_mapping = {
            'High School': 0,
            'Bachelor': 1,
            'Master': 2,
            'PhD': 3
        }
        education_val = education_mapping.get(form.education.data, 0)  # Default to 0 if not found
        
        self_emp_val   = 1 if form.self_employed.data == 'Yes' else 0   # Yes=1, No=0

        # Property area mapped to numbers: Urban=2, Semiurban=1, Rural=0
        property_map = {'Urban': 2, 'Semiurban': 1, 'Rural': 0}
        property_val = property_map[form.property_area.data]

        #  Step 2: Build the feature array 
        # numpy array with shape (1, 11) — one row, 11 features
        # The ORDER must match exactly what the model was trained on
        features = np.array([[
            gender_val,
            married_val,
            dependents_val,
            education_val,
            self_emp_val,
            float(form.applicant_income.data),
            float(form.coapplicant_income.data),
            float(form.loan_amount.data),
            float(form.loan_amount_term.data),
            float(form.credit_history.data),
            property_val
        ]])

        # Apply scaling if we have a scaler (for Logistic Regression)
        if scaler is not None:
            features = scaler.transform(features)

        #  Step 3: Run the ML Prediction 
        if model:
            # model.predict() returns [0] or [1]
            pred_raw  = model.predict(features)[0]

            # model.predict_proba() returns probability for each class [P(reject), P(approve)]
            pred_prob = model.predict_proba(features)[0]

            # Convert 1/0 to human-readable label
            result      = 'Approved' if pred_raw == 1 else 'Rejected'

            # Get the highest probability (confidence of the prediction) as a percentage
            probability = round(max(pred_prob) * 100, 1)
        else:
            # Fallback if model file isn't ready yet — for testing purposes only
            result      = 'Approved'
            probability = 78.5

        #  Step 4: Save to Database (only for logged-in users) 
        # Guest users can still get predictions, but results won't be saved
        if current_user.is_authenticated:
            application = LoanApplication(
                user_id            = current_user.id,
                gender             = form.gender.data,
                married            = form.married.data,
                dependents         = form.dependents.data,
                education          = form.education.data,  # Saves the actual text value
                self_employed      = form.self_employed.data,
                applicant_income   = form.applicant_income.data,
                coapplicant_income = form.coapplicant_income.data,
                loan_amount        = form.loan_amount.data,
                loan_amount_term   = float(form.loan_amount_term.data),
                credit_history     = float(form.credit_history.data),
                property_area      = form.property_area.data,
                prediction         = result,
                probability        = probability
            )
            db.session.add(application)    # Stage the new record
            db.session.commit()            # Write it to the database

        #  Step 5: Show the result page with prediction data 
        return render_template('result.html',
            result           = result,
            probability      = probability,
            applicant_income = int(form.applicant_income.data),
            loan_amount      = int(form.loan_amount.data),
            credit_history   = int(float(form.credit_history.data)),
            loan_term        = form.loan_amount_term.data
        )

    # If GET request or validation failed → show the form again
    return render_template('predict.html', form=form)


@main.route('/dashboard')
def dashboard():
    """
    Analytics Dashboard route.
    Queries all saved loan applications from the DB and computes:
    - Overall stats (totals, rates)
    - Chart data (income brackets, credit history breakdown)
    - Model performance metrics (loaded from metrics.json)
    """

    # Fetch ALL loan applications from the database
    apps  = LoanApplication.query.all()
    total    = len(apps)
    approved = sum(1 for a in apps if a.prediction == 'Approved')
    rejected = total - approved

    # Calculate approval/rejection rates as percentages
    # Avoid division by zero if no applications exist yet
    approval_rate  = round((approved / total * 100), 1) if total else 0
    rejection_rate = round((rejected / total * 100), 1) if total else 0

    #  Load Model Performance Metrics 
    # metrics.json was saved by train_model.py after training
    metrics_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'metrics.json')
    accuracy, precision, recall, f1 = 0, 0, 0, 0
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            m         = json.load(f)
            accuracy  = m.get('accuracy', 0)
            precision = m.get('precision', 0)
            recall    = m.get('recall', 0)
            f1        = m.get('f1_score', 0)  # Note: key is 'f1_score' from train_model.py

    # Bundle all stats into a dictionary to pass to the template
    stats = {
        'total':          total,
        'approval_rate':  approval_rate,
        'rejection_rate': rejection_rate,
        'accuracy':       round(accuracy * 100, 1) if accuracy else 0,    # Convert to percentage
        'precision':      round(precision * 100, 1) if precision else 0,
        'recall':         round(recall * 100, 1) if recall else 0,
        'f1':             round(f1 * 100, 1) if f1 else 0
    }

    #  Build Income Bracket Chart Data 
    # Groups applications into 5 income buckets and counts approved/rejected in each
    inc_approved = [0] * 5  # One counter per bracket
    inc_rejected = [0] * 5

    for a in apps:
        inc = a.applicant_income
        # Determine which income bracket this application falls into
        if   inc < 2000: idx = 0   # $0–2K
        elif inc < 4000: idx = 1   # $2K–4K
        elif inc < 6000: idx = 2   # $4K–6K
        elif inc < 8000: idx = 3   # $6K–8K
        else:            idx = 4   # $8K+

        if a.prediction == 'Approved': 
            inc_approved[idx] += 1
        else:                          
            inc_rejected[idx] += 1

    #  Build Credit History Chart Data 
    # Counts approved/rejected split by credit_history (0 = Bad, 1 = Good)
    cred_approved = [
        sum(1 for a in apps if a.credit_history == 0 and a.prediction == 'Approved'),
        sum(1 for a in apps if a.credit_history == 1 and a.prediction == 'Approved')
    ]
    cred_rejected = [
        sum(1 for a in apps if a.credit_history == 0 and a.prediction == 'Rejected'),
        sum(1 for a in apps if a.credit_history == 1 and a.prediction == 'Rejected')
    ]

    # All chart data passed to dashboard.html where Chart.js renders it visually
    chart_data = {
        'approved':        approval_rate,
        'rejected':        rejection_rate,
        'income_approved': inc_approved,
        'income_rejected': inc_rejected,
        'credit_approved': cred_approved,
        'credit_rejected': cred_rejected
    }

    return render_template('dashboard.html', stats=stats, chart_data=chart_data)


# ════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration route.
    - If already logged in → redirect to home (no need to register again)
    - GET → show empty registration form
    - POST → validate → check for duplicate email → hash password → save user
    """
    # Redirect already-logged-in users away from the register page
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():

        # Check if this email is already registered in the database
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('auth.login'))

        # Hash the password using Werkzeug's secure hashing
        # NEVER store plain text passwords — always store the hash
        hashed_pw = generate_password_hash(form.password.data)

        # Create a new User object and save it to the database
        user = User(
            username = form.username.data,
            email    = form.email.data,
            password = hashed_pw
        )
        db.session.add(user)
        db.session.commit()

        # Flash a success message shown on the next page
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login route.
    - GET → show login form
    - POST → find user by email → verify hashed password → create session
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():

        # Look up the user by their email address
        user = User.query.filter_by(email=form.email.data).first()

        # check_password_hash compares the entered password against the stored hash
        if user and check_password_hash(user.password, form.password.data):
            # login_user() creates a secure session so Flask-Login tracks this user
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')

            # 'next' parameter allows redirecting back to the page the user tried to visit
            # e.g., if they tried to go to /predict while logged out
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        # Generic error message — don't reveal whether email or password was wrong
        flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required  # Only logged-in users can log out
def logout():
    """
    Logout route.
    Clears the user's session and redirects to the home page.
    """
    logout_user()  # Flask-Login clears the session cookie
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))