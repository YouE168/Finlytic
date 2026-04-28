from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange


#  Auth Forms 

class RegisterForm(FlaskForm):
    username         = StringField('Full Name',
                           validators=[DataRequired(), Length(min=2, max=80)])
    email            = StringField('Email',
                           validators=[DataRequired(), Email()])
    password         = PasswordField('Password',
                           validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                           validators=[DataRequired(), EqualTo('password',
                               message='Passwords must match')])


class LoginForm(FlaskForm):
    email    = StringField('Email',    validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


#  Loan Prediction Form 

class LoanForm(FlaskForm):
    gender = SelectField('Gender', validators=[DataRequired()], choices=[
        ('', 'Select gender'),
        ('Male', 'Male'),
        ('Female', 'Female')
    ])

    married = SelectField('Married', validators=[DataRequired()], choices=[
        ('', 'Select status'),
        ('Yes', 'Yes'),
        ('No', 'No')
    ])

    dependents = SelectField('Dependents', validators=[DataRequired()], choices=[
        ('', 'Select dependents'),
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3+', '3+')
    ])

    education = SelectField('Education', choices=[
    ('', 'Select education'),  
    ('High School', 'High School'),
    ('Bachelor', 'Bachelor'), 
    ('Master', 'Master'),
    ('PhD', 'PhD')
], validators=[DataRequired()])

    self_employed = SelectField('Self Employed', validators=[DataRequired()], choices=[
        ('', 'Select status'),
        ('Yes', 'Yes'),
        ('No', 'No')
    ])

    applicant_income = FloatField('Applicant Income',
                            validators=[DataRequired(), NumberRange(min=0)])

    coapplicant_income = FloatField('Coapplicant Income',
                              validators=[DataRequired(), NumberRange(min=0)])

    loan_amount = FloatField('Loan Amount',
                       validators=[DataRequired(), NumberRange(min=1)])

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

    credit_history = SelectField('Credit History', validators=[DataRequired()], choices=[
        ('', 'Select history'),
        ('1', 'Good (1)'),
        ('0', 'Bad (0)')
    ])

    property_area = SelectField('Property Area', validators=[DataRequired()], choices=[
        ('', 'Select area'),
        ('Urban', 'Urban'),
        ('Semiurban', 'Semiurban'),
        ('Rural', 'Rural')
    ])