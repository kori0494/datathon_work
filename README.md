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
- [Output](#-outputs)

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

## 🧠 Phased Approach

The project is structured into clear, logical phases:

---

### 1️⃣ Exploratory & Prescriptive Analytics  
**(`Phase_1.ipynb`, `Phase_1_EDA.ipynb`)**

**Focus:** Extract business insights

- 📊 Promotion ROI analysis  
- 🔁 Return rate diagnostics  
- 👥 Customer segmentation (RFM)  
- 📅 Seasonal demand patterns  

---

### 2️⃣ Data Preprocessing & Feature Engineering  
**(`Phase_2.ipynb`)**

**Focus:** Build modeling dataset

- Aggregate daily metrics (sales, traffic, shipments)  
- Handle missing values & anomalies  
- Align timelines across datasets  

**Feature Engineering includes:**
- Lag features  
- Rolling statistics  
- Temporal signals  

---

### 3️⃣ Hybrid ML Forecasting  
**(`Phase_3.ipynb`)**

**Focus:** Long-term prediction

- Prophet captures:
  - Trend  
  - Seasonality  

- XGBoost models:
  - Residuals  
  - Promotions  
  - Demand spikes  

- Recursive forecasting for **548 days**  
- SHAP for model interpretability  

---

## 🛠️ Tech Stack

| Category | Tools |
|----------|------|
| Data Processing | `pandas`, `numpy` |
| Visualization | `matplotlib`, `seaborn` |
| Machine Learning | `scikit-learn`, `xgboost` |
| Time Series | `prophet` |
| Explainability | `shap` |
| Optimization | `optuna` |


## ▶️ Execution Order

Run notebooks in sequence:

Install initial independencies: pip install -r requirements.txt

[1] Phase_1.ipynb        → Data cleaning & auditing
[2] Phase_1_EDA.ipynb    → Exploration & insights
[3] Phase_2.ipynb        → Feature engineering
[4] Phase_3.ipynb        → Forecasting & SHAP analysis

## 📈 Outputs

The pipeline generates:

📊 Processed datasets (.csv)
📉 Forecast results (Revenue & COGS)
📌 Visualization plots (.png)
🔍 SHAP explanation plots

All outputs are saved in:

notebook/
