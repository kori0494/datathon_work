# 📊 E-Commerce Analytics & Revenue Forecasting

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🚀 End-to-end data science pipeline for analyzing e-commerce performance, generating actionable business insights, and forecasting long-term revenue & COGS using a **Prophet + XGBoost hybrid architecture**.

---

## 📖 Table of Contents

- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Directory Structure](#-directory-structure)
- [Phased Approach](#-phased-approach)
- [Tech Stack](#-tech-stack)
- [Execution Order](#-execution-order)
- [Outputs](#-outputs)

---

## 🚀 About the Project

This project implements a **complete machine learning and analytics workflow** for a multi-table e-commerce environment.

It transforms raw relational data (orders, customers, products, etc.) into:

- 📈 **548-day forecasts**
- 💰 Daily **Revenue & COGS predictions**
- 🔍 Deep **business insights**

The pipeline bridges **business intelligence** and **advanced machine learning**, enabling both:
- Strategic decision-making
- High-accuracy forecasting

---

## ✨ Key Features

- 🔗 **End-to-end pipeline** (raw data → insights → forecasting)
- 📊 **Advanced EDA & business analytics**
- 🧠 **Hybrid forecasting model**:
  - Prophet → trend & seasonality
  - XGBoost → residual patterns
- 🔍 **Explainable AI (SHAP)**
- 🔁 **Recursive multi-step forecasting (548 days)**
- ⚙️ **Robust feature engineering (lags, rolling stats)**

---

## 📂 Directory Structure

```text
├── notebook/
│   ├── csv/                    # Raw datasets (INPUT)
│   │   ├── orders.csv
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   └── ...
│   │
│   ├── baseline.ipynb          # Baseline model
│   ├── Phase_1.ipynb           # Data cleaning & auditing
│   ├── Phase_1_EDA.ipynb       # Exploratory data analysis
│   ├── Phase_2.ipynb           # Feature engineering
│   ├── Phase_3.ipynb           # Forecasting pipeline
│   │
│   ├── *.csv                   # Generated datasets (OUTPUT)
│   └── *.png                   # Generated plots (OUTPUT)
│
├── requirements.txt
└── README.md
