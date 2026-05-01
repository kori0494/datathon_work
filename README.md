# E-Commerce Analytics & Revenue Forecasting

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An end-to-end data science pipeline to analyze e-commerce performance, uncover actionable business insights, and forecast long-term revenue and costs using a Prophet + XGBoost hybrid architecture.

---

## 📖 Table of Contents

* [About the Project](#about-the-project)
* [Directory Structure](#directory-structure)
* [Phased Approach & Notebooks](#phased-approach--notebooks)
* [Tech Stack](#tech-stack)
* [Getting Started](#getting-started)
* [Execution Order](#execution-order)
* [License](#license)

---

## 🚀 About the Project

This repository contains a comprehensive Machine Learning and Data Analytics workflow built for a complex, multi-table e-commerce environment. It takes raw relational data (orders, customers, products, etc.) and transforms it into highly accurate, 548-day forecasts for Daily Revenue and Cost of Goods Sold (COGS). 

By leveraging Explainable AI (SHAP) and a hybrid time-series modeling approach, this project bridges the gap between deep exploratory business intelligence and advanced machine learning predictions.

---

## 📂 Directory Structure

The project relies on a specific directory structure to handle data inputs and outputs efficiently. 

* **Raw Data:** All original `.csv` files must be placed inside the `notebook/csv/` directory.
* **Outputs:** All generated files (processed datasets, model artifacts, and evaluation plots) are outputted directly to the root of the `notebook/` directory.
```text
├── notebook/
│   ├── csv/                    # Place all original raw datasets here
│   │   ├── orders.csv
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   └── ... (other raw tables)
│   ├── baseline.ipynb          # Model baseline establishment
│   ├── Phase_1.ipynb           # Data Cleaning, Auditing
│   ├── Phase_1_EDA.ipynb       # Exploratory Data Analysis
│   ├── Phase_2.ipynb           # Data Preprocessing 
│   ├── Phase_3.ipynb # Core ML Forecasting pipeline
│   ├── [generated_outputs].csv # Outputs are saved here automatically
│   └── [generated_plots].png   # Visualizations are saved here automatically
├── requirements.txt            # Python dependencies
└── README.md

🗂️ PHASED APPROACH & NOTEBOOKS
The pipeline is split into logical phases, documented across multiple Jupyter Notebooks.

1️⃣ Exploratory & Prescriptive Analytics (`Phase_1.ipynb`, `Phase_1_EDA.ipynb`)
Extracts actionable business insights from the relational database.

➤ Promotion ROI: Analyzes which promotional campaigns drive profitable growth.
➤ Return Rate Deep-Dive: Identifies key drivers behind product returns.
➤ Customer Segmentation: Segments users using RFM (Recency, Frequency, Monetary) to find "Golden Customers."
➤ Seasonal Demand Planning: Maps historical seasonal trends for inventory optimization.

2️⃣ Data Preprocessing & Feature Engineering (`Phase_2.ipynb`)
Wrangling raw dimensional tables into a unified, time-series-ready format.

➤ Aggregates daily operational metrics (sales, traffic, shipments).
➤ Handles missing values, aligns timelines, and addresses anomalies.
➤ Generates rolling aggregates and temporal lag features required for advanced modeling.

3️⃣ Hybrid ML Forecasting (`Phase_3.ipynb`)
Forecasts Daily Revenue and COGS over an extensive 548-day horizon.

➤ Prophet + XGBoost Hybrid: Uses Meta's Prophet to capture macro trends and seasonality. XGBoost is applied to predict the residuals (traffic spikes, momentum, promotional impacts).
➤ Recursive Forecasting: Implements dynamic lag mechanisms updated day-by-day throughout the test period.
➤ Model Explainability: Integrates SHAP to interpret feature importance and explain the drivers of the XGBoost predictions.

────────────────────────────────────────

🛠️ TECH STACK

⬩ Data Manipulation: pandas, numpy
⬩ Data Visualization: matplotlib, seaborn
⬩ Time Series & Machine Learning: prophet, xgboost, scikit-learn
⬩ Explainable AI & Hyperparameter Tuning: shap, optuna

────────────────────────────────────────

🏃‍♂️ EXECUTION ORDER

To reproduce the full pipeline and avoid missing data dependencies, run the notebooks in the `notebook/` directory in the following order:

[ 1 ] `Phase_1.ipynb` (For Data Cleaning, Auditing)
[ 2 ] `Phase_1_EDA.ipynb` (For data exploration and business intelligence)
[ 3 ] `Phase_2.ipynb` (To generate the final merged and cleaned dataset for modeling)
[ 4 ] `Phase_3.ipynb` (To train the final hybrid model, generate predictions, and output SHAP explanations)
