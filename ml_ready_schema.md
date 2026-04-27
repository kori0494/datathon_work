# ML-Ready Dataset Schema
> **Path**: `notebook/csv/ml_ready/`
> **Purpose**: Leak-free, chronologically-correct datasets for Datathon sales forecasting.

---

## Overview

| File | Rows | Cols | Dataset | Role |
|------|-----:|-----:|---------|------|
| `ts_train.csv` | 3 103 | 34 | Time-Series | Train (≤ 2021-12-31) |
| `ts_val.csv` | 181 | 34 | Time-Series | Validation (2022-01-01 – 2022-06-30) |
| `ts_test.csv` | 184 | 34 | Time-Series | Test (> 2022-06-30) |
| `ml_time_series.csv` | 3 833 | 34 | Time-Series | Full (all rows, unsplit) |
| `ml_customer_propensity.csv` | 88 924 | 18 | Customer | Full customer table |
| `cust_train.csv` | 65 550 | 18 | Customer | Train subset |
| `cust_test.csv` | 23 374 | 18 | Customer | Test subset |
| `ml_product_inventory.csv` | 1 624 | 17 | Product | Full product table (with GMROI) |
| `product_train.csv` | 1 624 | 14 | Product | Training (legacy format) |

---

## 1. Time-Series Files
> `ts_train.csv` · `ts_val.csv` · `ts_test.csv` · `ml_time_series.csv`
>
> **Target columns**: `Daily_Revenue`, `Daily_COGS`
> **Date column**: `order_date` — drop before `.fit()`

| # | Column | Dtype | Role | Description |
|---|--------|-------|------|-------------|
| 1 | `order_date` | str (date) | ID | Date of aggregation |
| 2 | `Daily_Revenue` | float64 | **TARGET** | Sum of Net_Revenue for the day |
| 3 | `Daily_COGS` | float64 | **TARGET** | Sum of COGS_line for the day |
| 4 | `Total_Units_Sold` | int64 | Feature | Total units sold |
| 5 | `Total_Orders` | int64 | Feature | Unique orders count |
| 6 | `Active_Promos` | int64 | Feature | Items sold under a promo |
| 7 | `N_Active_Promos` | int64 | Feature | Number of active promotions |
| 8 | `Day_of_Week` | int64 | Feature | 0=Mon … 6=Sun |
| 9 | `Month` | int64 | Feature | 1–12 |
| 10 | `Quarter` | int64 | Feature | 1–4 |
| 11 | `Year` | int64 | Feature | Calendar year |
| 12 | `Day_of_Year` | int64 | Feature | 1–366 |
| 13 | `Is_Weekend` | int64 | Feature | 1 if Sat/Sun |
| 14 | `Is_Month_End` | int64 | Feature | 1 if last day of month |
| 15 | `Is_Quarter_End` | int64 | Feature | 1 if last day of quarter |
| 16 | `Is_Public_Holiday` | int64 | Feature | 1 on VN public holidays (1/1, 30/4, 1/5, 2/9) |
| 17 | `Is_Mega_Sale` | int64 | Feature | 1 on 11.11 / 12.12 / Black Friday / Tết window |
| 18 | `Total_Sessions` | float64 | Feature | Web sessions that day |
| 19 | `Avg_Bounce_Rate` | float64 | Feature | Mean bounce rate |
| 20 | `Avg_Session_Dur` | float64 | Feature | Mean session duration (seconds) |
| 21 | `Revenue_Lag_1D` | float64 | Feature | Revenue at T−1 |
| 22 | `COGS_Lag_1D` | float64 | Feature | COGS at T−1 |
| 23 | `Revenue_Lag_7D` | float64 | Feature | Revenue at T−7 |
| 24 | `COGS_Lag_7D` | float64 | Feature | COGS at T−7 |
| 25 | `Revenue_Lag_30D` | float64 | Feature | Revenue at T−30 |
| 26 | `COGS_Lag_30D` | float64 | Feature | COGS at T−30 |
| 27 | `Revenue_Lag_365D` | float64 | Feature | Revenue at T−365 (same day last year) |
| 28 | `COGS_Lag_365D` | float64 | Feature | COGS at T−365 |
| 29 | `Revenue_Rolling_7D` | float64 | Feature | 7-day rolling mean of Revenue (`shift(1)` applied — no look-ahead) |
| 30 | `Sessions_Rolling_7D` | float64 | Feature | 7-day rolling mean of Sessions (`shift(1)` applied) |
| 31 | `Revenue_Rolling_30D` | float64 | Feature | 30-day rolling mean of Revenue (`shift(1)` applied) |
| 32 | `Sessions_Rolling_30D` | float64 | Feature | 30-day rolling mean of Sessions (`shift(1)` applied) |
| 33 | `Daily_Returns` | float64 | Feature | Total returned items that day |
| 34 | `Return_Rate` | float64 | Feature | returned_items / total_items_sold |

> **Leakage fix**: All lag and rolling features use `.shift(1)` — value at row T uses only data from T−1 and earlier. First 365 rows (warmup period) are dropped.

### Chronological Split Boundaries
| Split | Start | End | Rows |
|-------|-------|-----|-----:|
| Train | 2013-07-04 | 2021-12-31 | 3 103 |
| Val | 2022-01-01 | 2022-06-30 | 181 |
| Test | 2022-07-01 | 2022-12-31 | 184 |

---

## 2. Customer Propensity Files
> `ml_customer_propensity.csv` · `cust_train.csv` · `cust_test.csv`
>
> **Target column**: `TARGET_Bought_in_2022`
> **ID column**: `customer_id` — drop before `.fit()`

| # | Column | Dtype | Role | Description |
|---|--------|-------|------|-------------|
| 1 | `customer_id` | int64 | ID | Customer identifier |
| 2 | `Recency_Days` | int64 | Feature | Days since last purchase (snapshot = 2021-12-31) |
| 3 | `Frequency` | int64 | Feature | Number of unique orders placed before 2022 |
| 4 | `Monetary` | float64 | Feature | Total Net_Revenue generated before 2022 |
| 5 | `Avg_Order_Value` | float64 | Feature | Monetary / Frequency |
| 6 | `TARGET_Bought_in_2022` | int64 | **TARGET** | 1 if customer placed any order in 2022 |
| 7 | `Total_Spend_In_2022` | float64 | **EXCLUDE** | Actual 2022 spend — leaks the target period, always drop from X |
| 8 | `Avg_Review_Rating` | float64 | Feature | Mean review rating (pre-2022 reviews only) |
| 9 | `Total_Return_Orders` | float64 | Feature | Number of returned orders |
| 10 | `Return_Rate` | float64 | Feature | returned_orders / total_orders (same unit) |
| 11 | `region_enc` | float64 | Feature | Target-encoded region (mean Monetary per region, fit on train only) |
| 12 | `acquisition_channel_enc` | float64 | Feature | Target-encoded acquisition channel |
| 13 | `age_group_25-34` | bool | Feature | One-hot: age group 25–34 (base = 18–24) |
| 14 | `age_group_35-44` | bool | Feature | One-hot: age group 35–44 |
| 15 | `age_group_45-54` | bool | Feature | One-hot: age group 45–54 |
| 16 | `age_group_55+` | bool | Feature | One-hot: age group 55+ |
| 17 | `gender_Male` | bool | Feature | One-hot: Male (base = Female) |
| 18 | `gender_Non-binary` | bool | Feature | One-hot: Non-binary |

> **Class imbalance**: Positive rate ≈ 26%. Use `class_weight='balanced'` or SMOTE.
> **Always exclude** `Total_Spend_In_2022` from feature matrix X.

### Customer Split Logic
| File | Rows | Split rule |
|------|-----:|-----------|
| `cust_train.csv` | 65 550 | `Recency_Days > 365` — last purchase before 2021 |
| `cust_test.csv` | 23 374 | `Recency_Days ≤ 365` — active in 2021–2022 window |

---

## 3. Product Inventory Files
> `ml_product_inventory.csv` · `product_train.csv`
>
> **Target column**: `TARGET_Stockout_Risk_30d`
> **ID column**: `product_id` — drop before `.fit()`

### `ml_product_inventory.csv` — 1 624 rows × 17 cols (includes GMROI)

| # | Column | Dtype | Role | Description |
|---|--------|-------|------|-------------|
| 1 | `product_id` | int64 | ID | Product identifier |
| 2 | `avg_monthly_units_sold` | float64 | Feature | Mean units sold per month across all inventory snapshots |
| 3 | `avg_stock_on_hand` | float64 | Feature | Mean stock level across all monthly snapshots |
| 4 | `avg_fill_rate` | float64 | Feature | Mean fill rate |
| 5 | `avg_sell_through` | float64 | Feature | Mean sell-through rate |
| 6 | `avg_stockout_days` | float64 | Feature | Mean stockout days per month |
| 7 | `n_months` | int64 | Feature | Months of inventory history available |
| 8 | `price` | float64 | Feature | Average selling price |
| 9 | `cogs` | float64 | Feature | Average cost of goods sold |
| 10 | `Gross_Margin_Pct` | float64 | Feature | (price − cogs) / price |
| 11 | `Daily_Velocity` | float64 | Feature | avg_monthly_units_sold / 30 |
| 12 | `GMROI` | float64 | Feature | Gross Margin Return on Average Inventory Investment |
| 13 | `TARGET_Stockout_Risk_30d` | int64 | **TARGET** | 1 if current stock will be exhausted within 30 days |
| 14 | `stock_on_hand` | int64 | Feature | Latest stock snapshot value |
| 15 | `category_GenZ` | bool | Feature | One-hot: category = GenZ (base = Casual) |
| 16 | `category_Outdoor` | bool | Feature | One-hot: category = Outdoor |
| 17 | `category_Streetwear` | bool | Feature | One-hot: category = Streetwear |

**GMROI formula**:
```
Avg_Inventory_Cost = mean(stock_on_hand) × cogs   # averaged over all monthly snapshots
Annualized_Revenue = avg_monthly_units_sold × price × 12
GMROI = (Annualized_Revenue × Gross_Margin_%) / Avg_Inventory_Cost
```

### `product_train.csv` — 1 624 rows × 14 cols (legacy format, no GMROI / n_months)

| # | Column | Dtype | Role |
|---|--------|-------|------|
| 1 | `product_id` | int64 | ID |
| 2 | `avg_monthly_units_sold` | float64 | Feature |
| 3 | `avg_fill_rate` | float64 | Feature |
| 4 | `avg_sell_through` | float64 | Feature |
| 5 | `avg_stockout_days` | float64 | Feature |
| 6 | `price` | float64 | Feature |
| 7 | `cogs` | float64 | Feature |
| 8 | `Gross_Margin_Pct` | float64 | Feature |
| 9 | `Daily_Velocity` | float64 | Feature |
| 10 | `TARGET_Stockout_Risk_30d` | int64 | **TARGET** |
| 11 | `stock_on_hand` | int64 | Feature |
| 12 | `category_GenZ` | bool | Feature |
| 13 | `category_Outdoor` | bool | Feature |
| 14 | `category_Streetwear` | bool | Feature |

> **Class imbalance**: Positive rate ≈ 0.3%. Extremely imbalanced — use SMOTE or `class_weight={0: 1, 1: ~300}`.

---

## Quick-Start Code

```python
import pandas as pd

ML = "notebook/csv/ml_ready"

# ── Time-Series ─────────────────────────────────────────────────────────────
TARGET_TS = ["Daily_Revenue", "Daily_COGS"]
DROP_TS   = TARGET_TS + ["order_date"]

ts_train = pd.read_csv(f"{ML}/ts_train.csv", parse_dates=["order_date"])
ts_val   = pd.read_csv(f"{ML}/ts_val.csv",   parse_dates=["order_date"])
ts_test  = pd.read_csv(f"{ML}/ts_test.csv",  parse_dates=["order_date"])

X_train_ts, y_train_ts = ts_train.drop(columns=DROP_TS), ts_train[TARGET_TS]
X_val_ts,   y_val_ts   = ts_val.drop(columns=DROP_TS),   ts_val[TARGET_TS]
X_test_ts,  y_test_ts  = ts_test.drop(columns=DROP_TS),  ts_test[TARGET_TS]

# ── Customer Propensity ─────────────────────────────────────────────────────
TARGET_CUST = ["TARGET_Bought_in_2022"]
DROP_CUST   = TARGET_CUST + ["customer_id", "Total_Spend_In_2022"]

cust   = pd.read_csv(f"{ML}/ml_customer_propensity.csv")
X_cust = cust.drop(columns=DROP_CUST, errors="ignore")
y_cust = cust[TARGET_CUST]

# ── Product Inventory ───────────────────────────────────────────────────────
TARGET_PROD = ["TARGET_Stockout_Risk_30d"]
DROP_PROD   = TARGET_PROD + ["product_id"]

prod   = pd.read_csv(f"{ML}/ml_product_inventory.csv")
X_prod = prod.drop(columns=DROP_PROD, errors="ignore")
y_prod = prod[TARGET_PROD]
```
