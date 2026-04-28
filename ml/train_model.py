# train_model.py – The AI/ML heart of Finlytic
# This script is run ONCE (offline) to train the loan prediction model
# It reads the Kaggle dataset, preprocesses it, trains two models,
# picks the best one, and saves it as model.pkl for the web app to use

import pandas as pd
import numpy as np
import joblib
import json
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def main():
    # Load the dataset - update this path to where your CSV actually is
    df = pd.read_csv('ml/dataset.csv')
    
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Original education values: {df['Education'].unique()}")
    
    # Handle missing values
    df['Gender'] = df['Gender'].fillna(df['Gender'].mode()[0])
    df['Married'] = df['Married'].fillna(df['Married'].mode()[0])
    df['Dependents'] = df['Dependents'].fillna('0')
    df['Self_Employed'] = df['Self_Employed'].fillna(df['Self_Employed'].mode()[0])
    df['LoanAmount'] = df['LoanAmount'].fillna(df['LoanAmount'].median())
    df['Loan_Amount_Term'] = df['Loan_Amount_Term'].fillna(df['Loan_Amount_Term'].mode()[0])
    df['Credit_History'] = df['Credit_History'].fillna(df['Credit_History'].mode()[0])
    
    # Encode categorical variables
    df['Gender'] = df['Gender'].map({'Male': 1, 'Female': 0})
    df['Married'] = df['Married'].map({'Yes': 1, 'No': 0})
    
    # Encode Education - check what values exist in your dataset
    # If your dataset has 'Graduate'/'Not Graduate', map them to numeric values
    # If your dataset has 'High School'/'Bachelor'/'Master'/'PhD', use that mapping
    unique_edu = df['Education'].unique()
    
    if 'Graduate' in unique_edu or 'Not Graduate' in unique_edu:
        # Original Kaggle dataset
        print("Using original Kaggle education values (Graduate/Not Graduate)")
        df['Education'] = df['Education'].map({'Graduate': 1, 'Not Graduate': 0})
    else:
        # New education values
        print("Using new education values (High School/Bachelor/Master/PhD)")
        education_mapping = {
            'High School': 0,
            'Bachelor': 1,
            'Master': 2,
            'PhD': 3
        }
        df['Education'] = df['Education'].map(education_mapping)
    
    df['Self_Employed'] = df['Self_Employed'].map({'Yes': 1, 'No': 0})
    df['Property_Area'] = df['Property_Area'].map({'Urban': 2, 'Semiurban': 1, 'Rural': 0})
    df['Dependents'] = df['Dependents'].replace('3+', 3).astype(int)
    
    # Define features (X) and target (y)
    feature_columns = ['Gender', 'Married', 'Dependents', 'Education', 'Self_Employed',
                       'ApplicantIncome', 'CoapplicantIncome', 'LoanAmount', 
                       'Loan_Amount_Term', 'Credit_History', 'Property_Area']
    
    X = df[feature_columns]
    y = df['Loan_Status'].map({'Y': 1, 'N': 0})
    
    # Check for any NaN values and handle them
    print(f"\nChecking for NaN values in features...")
    if X.isnull().any().any():
        print("NaN values found. Filling with 0...")
        X = X.fillna(0)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features for Logistic Regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Logistic Regression
    lr_model = LogisticRegression(max_iter=1000, random_state=42)
    lr_model.fit(X_train_scaled, y_train)
    lr_pred = lr_model.predict(X_test_scaled)
    
    # Train Random Forest
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    
    # Compare models
    lr_accuracy = accuracy_score(y_test, lr_pred)
    rf_accuracy = accuracy_score(y_test, rf_pred)
    
    print(f"\nLogistic Regression Accuracy: {lr_accuracy:.4f}")
    print(f"Random Forest Accuracy: {rf_accuracy:.4f}")
    
    # Print classification report for the best model
    if lr_accuracy >= rf_accuracy:
        best_model = lr_model
        scaler_for_best = scaler
        print(f"\nSelected: Logistic Regression")
        from sklearn.metrics import classification_report
        print("\nClassification Report:")
        print(classification_report(y_test, lr_pred, target_names=['Rejected', 'Approved']))
    else:
        best_model = rf_model
        scaler_for_best = None
        print(f"\nSelected: Random Forest")
        from sklearn.metrics import classification_report
        print("\nClassification Report:")
        print(classification_report(y_test, rf_pred, target_names=['Rejected', 'Approved']))
    
    # Save the model
    joblib.dump(best_model, 'ml/model.pkl')
    
    # Save the scaler if using Logistic Regression
    if scaler_for_best:
        joblib.dump(scaler_for_best, 'ml/scaler.pkl')
        print("✅ Scaler saved to ml/scaler.pkl")
    
    # Save metrics
    y_pred = lr_pred if lr_accuracy >= rf_accuracy else rf_pred
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred)),
        'recall': float(recall_score(y_test, y_pred)),
        'f1_score': float(f1_score(y_test, y_pred))
    }
    
    with open('ml/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
    
    print(f"\n✅ Metrics saved to ml/metrics.json")
    print(f"   Accuracy: {metrics['accuracy']:.2%}")
    print(f"   Precision: {metrics['precision']:.2%}")
    print(f"   Recall: {metrics['recall']:.2%}")
    print(f"   F1 Score: {metrics['f1_score']:.2%}")
    print("\n🎉 Training complete! Your model is ready.")
    print("   Run `python run.py` to start the web app.")

if __name__ == "__main__":
    main()