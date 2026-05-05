# ============================================================
# FILE: routes.py
# PURPOSE: Handles all URL routing and business logic for Finlytic
# DESCRIPTION: This is the BACKBONE of the application. A "route" maps a URL 
#              (like /predict or /dashboard) to a Python function that handles it.
#              We use Flask Blueprints to organize routes into two groups:
#              - main: Public pages (home, predict, dashboard)
#              - auth: Authentication pages (register, login, logout)
# ============================================================

# ============================================================
# IMPORTS
# ============================================================
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

# ============================================================
# CREATE BLUEPRINTS
# ============================================================
# Blueprints group related routes together like "mini Flask apps"
# This keeps code organized and maintainable
main = Blueprint('main', __name__)   # Public pages: home, predict, dashboard
auth = Blueprint('auth', __name__)   # Authentication pages: register, login, logout

# ============================================================
# LOAD THE ML MODEL AND SCALER AT STARTUP
# ============================================================
# We load the model ONCE when the app starts (not on every request)
# This makes predictions much faster because loading a model from disk is slow
# If we loaded on every request, the app would be very slow

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'scaler.pkl')
model = None
scaler = None

# Try to load the trained machine learning model
if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
    try:
        model = joblib.load(MODEL_PATH)  # Load the Random Forest/Logistic Regression model
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"⚠️ Model not loaded: {e}")

# Try to load the scaler (normalizes input data before prediction)
if os.path.exists(SCALER_PATH) and os.path.getsize(SCALER_PATH) > 0:
    try:
        scaler = joblib.load(SCALER_PATH)  # Load the StandardScaler
        print("✅ Scaler loaded successfully")
    except Exception as e:
        print(f"⚠️ Scaler not loaded: {e}")


# ════════════════════════════════════════════════════════════
#  MAIN ROUTES (Public Pages)
# ════════════════════════════════════════════════════════════

@main.route('/')
def index():
    """
    Home page route.
    URL: / (root)
    Just renders the landing page — no data processing needed.
    This is the first page users see when they visit the website.
    """
    return render_template('index.html')


@main.route('/predict', methods=['GET', 'POST'])
def predict():
    """
    Loan Prediction route — the CORE FEATURE of Finlytic.
    URL: /predict
    
    GET request:  User visits /predict → show the empty loan form
    POST request: User submits the form → validate → predict → show result
    
    This is where the magic happens: form data → ML model → prediction result
    """
    form = LoanForm()  # Create a new form instance

    # form.validate_on_submit() returns True only when:
    # 1. The request is POST (form was submitted)
    # 2. All validators pass (no empty fields, valid numbers, etc.)
    if form.validate_on_submit():

        # ========================================================
        # Step 1: Encode form inputs to match ML model training format
        # ========================================================
        # The model was trained on NUMBERS, not strings
        # So we convert text values → integers/floats exactly as done during training

        gender_val = 1 if form.gender.data == 'Male' else 0         # Male=1, Female=0
        married_val = 1 if form.married.data == 'Yes' else 0         # Yes=1, No=0
        
        # Handle '3+' special case - convert to integer 3
        dependents_val = 3 if form.dependents.data == '3+' else int(form.dependents.data)
        
        # Map education from form options to numeric values that match training
        # The model expects numbers, not text like "Bachelor"
        education_mapping = {
            'High School': 0,
            'Bachelor': 1,
            'Master': 2,
            'PhD': 3
        }
        education_val = education_mapping.get(form.education.data, 0)  # Default to 0 if not found
        
        self_emp_val = 1 if form.self_employed.data == 'Yes' else 0   # Yes=1, No=0

        # Property area mapped to numbers: Urban=2, Semiurban=1, Rural=0
        property_map = {'Urban': 2, 'Semiurban': 1, 'Rural': 0}
        property_val = property_map[form.property_area.data]

        # ========================================================
        # Step 2: Build the feature array (input for ML model)
        # ========================================================
        # numpy array with shape (1, 11) — one row (single prediction), 11 features
        # The ORDER of features MUST match exactly what the model was trained on
        # If the order is wrong, the prediction will be incorrect!
        features = np.array([[
            gender_val,           # Feature 0: Gender (0=Female, 1=Male)
            married_val,          # Feature 1: Married (0=No, 1=Yes)
            dependents_val,       # Feature 2: Number of dependents (0,1,2,3)
            education_val,        # Feature 3: Education level (0,1,2,3)
            self_emp_val,         # Feature 4: Self employed (0=No, 1=Yes)
            float(form.applicant_income.data),    # Feature 5: Applicant income
            float(form.coapplicant_income.data),  # Feature 6: Co-applicant income
            float(form.loan_amount.data),         # Feature 7: Loan amount requested
            float(form.loan_amount_term.data),    # Feature 8: Loan term in months
            float(form.credit_history.data),      # Feature 9: Credit history (0=Bad, 1=Good)
            property_val          # Feature 10: Property area (0=Rural, 1=Semiurban, 2=Urban)
        ]])

        # Apply scaling if we have a scaler (required for Logistic Regression)
        # Scaling normalizes data so all features are on the same scale (e.g., 0-1)
        # This improves model accuracy
        if scaler is not None:
            features = scaler.transform(features)

        # ========================================================
        # Step 3: Run the ML Prediction
        # ========================================================
        if model:
            # model.predict() returns [0] for Rejected or [1] for Approved
            pred_raw = model.predict(features)[0]

            # model.predict_proba() returns probability for each class
            # Format: [P(Rejected), P(Approved)] - values between 0 and 1
            pred_prob = model.predict_proba(features)[0]

            # Convert 1/0 to human-readable label
            result = 'Approved' if pred_raw == 1 else 'Rejected'

            # Get the highest probability (confidence of the prediction) as a percentage
            # max(pred_prob) takes the higher of the two probabilities
            # Multiply by 100 to get percentage, round to 1 decimal place
            probability = round(max(pred_prob) * 100, 1)
        else:
            # Fallback if model file isn't ready yet — for testing purposes only
            # This should not happen in production
            result = 'Approved'
            probability = 78.5

        # ========================================================
        # Step 4: Save to Database (only for logged-in users)
        # ========================================================
        # Guest users can still get predictions, but results won't be saved
        # This allows users to try the feature before creating an account
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
            db.session.add(application)    # Stage the new record (add to transaction)
            db.session.commit()            # Write it to the database (save permanently)

        # ========================================================
        # Step 5: Show the result page with prediction data
        # ========================================================
        # Pass the prediction results to result.html template
        return render_template('result.html',
            result           = result,
            probability      = probability,
            applicant_income = int(form.applicant_income.data),
            loan_amount      = int(form.loan_amount.data),
            credit_history   = int(float(form.credit_history.data)),
            loan_term        = form.loan_amount_term.data
        )

    # If GET request or validation failed → show the form again (with errors displayed)
    return render_template('predict.html', form=form)


@main.route('/dashboard')
@login_required  # This decorator ensures only logged-in users can access the dashboard
def dashboard():
    """
    Analytics Dashboard route.
    URL: /dashboard (requires login)
    
    Queries all saved loan applications from the DB and computes:
    - Overall stats (totals, approval/rejection rates)
    - Chart data (income brackets breakdown, credit history breakdown)
    - Model performance metrics (loaded from metrics.json)
    
    @login_required redirects to login page if user is not authenticated
    """
    # ========================================================
    # Fetch ALL loan applications from the database
    # ========================================================
    apps = LoanApplication.query.all()
    total = len(apps)
    approved = sum(1 for a in apps if a.prediction == 'Approved')
    rejected = total - approved

    # Calculate approval/rejection rates as percentages
    # Avoid division by zero if no applications exist yet (total = 0)
    approval_rate = round((approved / total * 100), 1) if total else 0
    rejection_rate = round((rejected / total * 100), 1) if total else 0

    # ========================================================
    # Load Model Performance Metrics from metrics.json
    # ========================================================
    # metrics.json was saved by train_model.py after training the model
    # Contains: accuracy, precision, recall, f1_score
    metrics_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'metrics.json')
    accuracy, precision, recall, f1 = 0, 0, 0, 0
    
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            m = json.load(f)
            accuracy = m.get('accuracy', 0)
            precision = m.get('precision', 0)
            recall = m.get('recall', 0)
            f1 = m.get('f1_score', 0)  # Note: key is 'f1_score' from train_model.py

    # Bundle all statistics into a dictionary to pass to the template
    stats = {
        'total':          total,
        'approval_rate':  approval_rate,
        'rejection_rate': rejection_rate,
        'accuracy':       round(accuracy * 100, 1) if accuracy else 0,  # Convert decimal to percentage
        'precision':      round(precision * 100, 1) if precision else 0,
        'recall':         round(recall * 100, 1) if recall else 0,
        'f1':             round(f1 * 100, 1) if f1 else 0
    }

    # ========================================================
    # Build Income Bracket Chart Data
    # ========================================================
    # Groups applications into 5 income buckets and counts approved/rejected in each
    # This data feeds the "Income vs Approval" bar chart on the dashboard
    inc_approved = [0] * 5  # One counter per bracket: [$0-2K, $2K-4K, $4K-6K, $6K-8K, $8K+]
    inc_rejected = [0] * 5  # Same for rejected applications

    for a in apps:
        inc = a.applicant_income
        # Determine which income bracket this application falls into
        if inc < 2000:
            idx = 0   # $0–2K
        elif inc < 4000:
            idx = 1   # $2K–4K
        elif inc < 6000:
            idx = 2   # $4K–6K
        elif inc < 8000:
            idx = 3   # $6K–8K
        else:
            idx = 4   # $8K+

        # Increment the appropriate counter based on prediction result
        if a.prediction == 'Approved':
            inc_approved[idx] += 1
        else:
            inc_rejected[idx] += 1

    # ========================================================
    # Build Credit History Chart Data
    # ========================================================
    # Counts approved/rejected split by credit_history (0 = Bad credit, 1 = Good credit)
    # This data feeds the "Credit Score Distribution" horizontal bar chart
    cred_approved = [
        sum(1 for a in apps if a.credit_history == 0 and a.prediction == 'Approved'),  # Bad credit, approved
        sum(1 for a in apps if a.credit_history == 1 and a.prediction == 'Approved')   # Good credit, approved
    ]
    cred_rejected = [
        sum(1 for a in apps if a.credit_history == 0 and a.prediction == 'Rejected'),  # Bad credit, rejected
        sum(1 for a in apps if a.credit_history == 1 and a.prediction == 'Rejected')   # Good credit, rejected
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


# ════════════════════════════════════════════════════════════
#  AUTHENTICATION ROUTES (User Account Management)
# ════════════════════════════════════════════════════════════

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration route.
    URL: /auth/register
    
    - GET request:  Show empty registration form
    - POST request: Validate input → check for duplicate email → hash password → save user
    - If already logged in → redirect to home page (no need to register again)
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
        # NEVER store plain text passwords in production — always store the hash!
        # Hashing transforms the password into a fixed-length string that cannot be reversed
        hashed_pw = generate_password_hash(form.password.data)

        # Create a new User object and save it to the database
        user = User(
            username = form.username.data,
            email    = form.email.data,
            password = hashed_pw
        )
        db.session.add(user)
        db.session.commit()

        # Flash a success message shown on the next page (login page)
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login route.
    URL: /auth/login
    
    - GET request:  Show login form
    - POST request: Find user by email → verify hashed password → create session
    """
    # Redirect already-logged-in users away from the login page
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    
    if form.validate_on_submit():
        # Look up the user by their email address
        user = User.query.filter_by(email=form.email.data).first()

        # Check if user exists AND password matches the stored hash
        # check_password_hash compares the entered password against the stored hash
        # It returns True if they match, False otherwise
        if user and check_password_hash(user.password, form.password.data):
            # login_user() creates a secure session so Flask-Login tracks this user
            # This is what keeps the user logged in across page requests
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')

            # 'next' parameter allows redirecting back to the page the user tried to visit
            # Example: if they tried to go to /dashboard while logged out, they're sent to login
            # After successful login, send them back to /dashboard instead of home
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        # Generic error message — don't reveal whether email or password was wrong
        # This is a security measure to prevent attackers from guessing valid emails
        flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required  # This decorator ensures only logged-in users can access logout
def logout():
    """
    Logout route.
    URL: /auth/logout (requires login)
    
    Clears the user's session and redirects to the home page.
    After logout, the user will need to login again to access protected pages.
    """
    logout_user()  # Flask-Login clears the session cookie
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


# ============================================================
# HOW THE FLOW WORKS (End-to-End Example):
# ============================================================
#
# Scenario: User applies for a loan
# ---------------------------------
# 1. User clicks "Apply" button → GET /predict
# 2. predict() function renders predict.html with empty form
# 3. User fills out form and clicks "Predict My Loan" → POST /predict
# 4. form.validate_on_submit() checks all fields
# 5. Form data is encoded into numerical features (gender→0/1, etc.)
# 6. Features array is created: [gender, married, dependents, education, ...]
# 7. If scaler exists, features are normalized
# 8. model.predict(features) returns 0 (Rejected) or 1 (Approved)
# 9. model.predict_proba(features) returns confidence score
# 10. If user is logged in, application is saved to database
# 11. render_template('result.html') shows prediction to user
# 12. User can try again or view dashboard for analytics
#
# ============================================================