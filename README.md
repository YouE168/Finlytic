# Finlytic - AI-Powered Loan Approval Prediction System

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-orange.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)

## 📋 Overview

**Finlytic** is a full-stack web application that uses supervised machine learning to predict whether a loan application will be approved or rejected. Users enter personal and financial information through an intuitive web form, and a trained ML model processes the input instantly, returning a prediction with a confidence score.

### Why This Project?

Traditional loan evaluation processes in many financial institutions are:

- 🐌 **Slow** - Takes days or weeks
- 🔄 **Inconsistent** - Different outcomes for similar profiles
- 👤 **Subjective** - Relies on manual screening

Finlytic demonstrates how AI can serve as a faster, more objective, and data-driven decision-support tool for lenders.

---

## 🚀 Live Demo Features

- ✅ **Real-time Predictions** - Get loan approval results in milliseconds
- 📊 **Analytics Dashboard** - Live charts showing approval rates, income patterns, and credit history distribution
- 🔐 **User Authentication** - Register/login to save your applications
- 📈 **Model Performance Metrics** - View accuracy, precision, recall, and F1 score
- 💾 **SQLite Database** - All submissions are saved for analysis

---

## 🛠️ Tech Stack

| Category             | Technologies                  |
| -------------------- | ----------------------------- |
| **Backend**          | Python, Flask, SQLAlchemy     |
| **Machine Learning** | scikit-learn, pandas, NumPy   |
| **Database**         | SQLite                        |
| **Frontend**         | Bootstrap 5, Chart.js, Jinja2 |
| **Authentication**   | Flask-Login, Werkzeug         |

---

## 📊 Model Performance

After training and comparing two algorithms:

| Model                   | Accuracy   | Precision | Recall     | F1 Score |
| ----------------------- | ---------- | --------- | ---------- | -------- |
| **Logistic Regression** | **78.86%** | 75.96%    | **98.75%** | 85.87%   |
| Random Forest           | 76.42%     | 74.00%    | 96.25%     | 83.50%   |

**Why Recall Matters:** With 98.75% recall, the model correctly identifies nearly all truly eligible applicants, minimizing the risk of wrongly rejecting qualified borrowers.

---

## 📁 Project Structure
