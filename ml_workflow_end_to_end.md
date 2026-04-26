# ML Workflow End-to-End — Datathon Sales Forecasting
> **Dataset**: `notebook/csv/ml_ready/` · **random_state = 42** ở mọi bước

---

## Mục lục

1. [Workflow 1 — Time-Series Forecasting](#1-workflow-1--time-series-forecasting)
2. [Workflow 2 — Customer Propensity](#2-workflow-2--customer-propensity)
3. [Workflow 3 — Product Inventory Risk](#3-workflow-3--product-inventory-risk)
4. [Tài liệu tham khảo](#4-tài-liệu-tham-khảo)

---

## 1. Workflow 1 — Time-Series Forecasting

**Files**: `ts_train.csv` · `ts_val.csv` · `ts_test.csv`  
**Targets**: `Daily_Revenue`, `Daily_COGS`  
**Drop trước `.fit()`**: `order_date`, `Daily_Revenue`, `Daily_COGS`

---

### Bước 1 — Baseline (Naive Forecast)

```python
# Lấy giá trị hôm qua đoán cho hôm nay
y_pred_baseline = ts_val["Revenue_Lag_1D"].values
```

Mốc so sánh: nếu model của bạn không beat được Naive thì có vấn đề về feature hoặc leakage.

---

### Bước 2 — Mô hình Hybrid: Prophet + XGBoost

#### 2a. Prophet — Tách Trend và Seasonality

**📄 Bài báo gốc**:
> Taylor, S. J., & Letham, B. (2018). **Forecasting at Scale**. *The American Statistician*, 72(1), 37–45.  
> DOI: [10.1080/00031305.2017.1380080](https://doi.org/10.1080/00031305.2017.1380080)  
> arXiv: [https://arxiv.org/abs/1701.09209](https://arxiv.org/abs/1701.09209)

**Prophet làm gì với dữ liệu của bạn?**

Prophet phân rã chuỗi thời gian thành phương trình cộng tính:

```
y(t) = g(t) + s(t) + h(t) + ε(t)
```

| Thành phần | Ý nghĩa | Biến trong dataset |
|---|---|---|
| `g(t)` | Piecewise-linear trend | Học từ `Daily_Revenue` qua 10 năm (2013–2021) |
| `s(t)` | Fourier-series seasonality | Tính mùa năm/tháng/tuần — được củng cố bởi `Month`, `Quarter`, `Day_of_Week` |
| `h(t)` | Holiday effects | **Biến ngoại sinh**: `Is_Public_Holiday` (1/1, 30/4, 1/5, 2/9), `Is_Mega_Sale` (11.11, 12.12, Black Friday, Tết) |
| `ε(t)` | Residual | Phần XGBoost sẽ học tiếp |

**Cách Prophet xử lý biến ngoại sinh (exogenous regressors)**:

Prophet cho phép thêm các cột bổ sung qua `add_regressor()`. Trong dataset của bạn:

```python
from prophet import Prophet

m = Prophet(yearly_seasonality=True, weekly_seasonality=True)

# Biến ngoại sinh được thêm vào Prophet
m.add_regressor("Is_Public_Holiday")   # Ngày lễ VN
m.add_regressor("Is_Mega_Sale")        # Mega Sale events
m.add_regressor("Is_Weekend")          # Weekend effect
m.add_regressor("Total_Sessions")      # Web traffic signal

df_prophet = ts_train.rename(columns={"order_date": "ds", "Daily_Revenue": "y"})
m.fit(df_prophet)
```

> **Lưu ý quan trọng**: Prophet KHÔNG dùng các Lag Features (`Revenue_Lag_7D`, `Revenue_Lag_365D`...) vì nó không có cơ chế xử lý autoregression. Phần này thuộc về XGBoost.

---

#### 2b. XGBoost — Học Residuals từ Biến Ngoại Sinh

**📄 Bài báo gốc**:
> Chen, T., & Guestrin, C. (2016). **XGBoost: A Scalable Tree Boosting System**. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794.  
> DOI: [10.1145/2939672.2939785](https://doi.org/10.1145/2939672.2939785)  
> arXiv: [https://arxiv.org/abs/1603.02754](https://arxiv.org/abs/1603.02754)

**XGBoost làm gì với dữ liệu của bạn?**

XGBoost xây dựng ensemble của cây quyết định theo kiểu **gradient boosting**. Mỗi cây mới học để sửa lỗi của cây trước:

```
Residual(t) = Daily_Revenue(t) - Prophet_Prediction(t)
```

XGBoost sau đó học `Residual(t)` từ tập biến ngoại sinh và lag features:

| Nhóm biến | Cột trong dataset | Vai trò |
|---|---|---|
| **Contextual (Binary)** | `Is_Mega_Sale`, `Is_Public_Holiday`, `Is_Weekend`, `Is_Month_End`, `Is_Quarter_End` | Capture spike ngắn hạn, không liên tục |
| **Lag Features** | `Revenue_Lag_1D`, `Revenue_Lag_7D`, `Revenue_Lag_30D`, `Revenue_Lag_365D` | Autoregressive signal — cung cấp "local context" mà Prophet thiếu |
| **Rolling Mean** | `Revenue_Rolling_7D`, `Revenue_Rolling_30D`, `Sessions_Rolling_7D` | Smoothed trend ngắn hạn |
| **Traffic** | `Total_Sessions`, `Avg_Bounce_Rate`, `Avg_Session_Dur` | Demand signal từ web analytics |
| **Operations** | `Total_Units_Sold`, `Total_Orders`, `Active_Promos`, `N_Active_Promos` | Supply-side và promotion signals |
| **Returns** | `Daily_Returns`, `Return_Rate` | Negative demand signal |

```python
import xgboost as xgb
import numpy as np

# Tính residual
prophet_pred_train = m.predict(df_prophet)["yhat"].values
residual_train = ts_train["Daily_Revenue"].values - prophet_pred_train

# Feature matrix cho XGBoost — dùng TẤT CẢ biến ngoại sinh + lag
DROP = ["Daily_Revenue", "Daily_COGS", "order_date"]
X_train = ts_train.drop(columns=DROP)
y_residual = residual_train

model_xgb = xgb.XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,        # sẽ được Optuna tune
    max_depth=6,               # sẽ được Optuna tune
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model_xgb.fit(X_train, y_residual)

# Dự báo cuối = Prophet + XGBoost residual correction
final_pred = prophet_pred + model_xgb.predict(X_val)
```

> **Tại sao Hybrid tốt hơn?** Prophet giỏi bắt xu hướng dài hạn và mùa vụ, nhưng bỏ sót các spike ngắn hạn (Flash Sale, holiday surge). XGBoost bù đắp đúng chỗ đó thông qua lag features và contextual variables.

---

### Bước 3 — Time-Series Cross-Validation (Expanding Window)

```
|---Train 2013-2018---|---Val 2019---|
|---Train 2013-2019---|---Val 2020---|
|---Train 2013-2020---|---Val 2021---|  ← fold cuối trước test
```

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=3, gap=0)
for fold, (train_idx, val_idx) in enumerate(tscv.split(ts_train)):
    X_fold_train = X_train.iloc[train_idx]
    X_fold_val   = X_train.iloc[val_idx]
    # ... fit và evaluate
```

---

### Bước 4 — Hyperparameter Tuning với Optuna

**📄 Bài báo gốc**:
> Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). **Optuna: A Next-generation Hyperparameter Optimization Framework**. *Proceedings of the 25th ACM SIGKDD International Conference*, 2623–2631.  
> DOI: [10.1145/3292500.3330701](https://doi.org/10.1145/3292500.3330701)  
> arXiv: [https://arxiv.org/abs/1907.10902](https://arxiv.org/abs/1907.10902)

**Optuna làm gì?**

Optuna dùng **Tree-structured Parzen Estimator (TPE)** — một dạng Bayesian optimization — để tìm hyperparameter tốt nhất nhanh hơn grid search tối đa 10–20 lần.

```python
import optuna

def objective(trial):
    params = {
        "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth":        trial.suggest_int("max_depth", 3, 10),
        "n_estimators":     trial.suggest_int("n_estimators", 100, 800),
        "subsample":        trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "random_state":     42
    }
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_residual)
    pred = model.predict(X_val)
    wape = np.sum(np.abs(y_val_residual - pred)) / np.sum(np.abs(y_val_residual))
    return wape  # minimize

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=100)
print(study.best_params)
```

**Metric mục tiêu**:

| Metric | Công thức | Ý nghĩa |
|---|---|---|
| WAPE | `Σ|y - ŷ| / Σ|y|` | Weighted, robust với outliers |
| RMSE | `√(Σ(y - ŷ)²/n)` | Penalize large errors nặng hơn |

---

### Bước 5 — Inference và Submission

```python
# Dự báo 184 ngày test (2022-07-01 → 2022-12-31)
prophet_test_pred = m.predict(df_test_prophet)["yhat"].values
xgb_residual_pred = model_xgb.predict(X_test)

submission = pd.DataFrame({
    "order_date":    ts_test["order_date"],
    "Daily_Revenue": prophet_test_pred + xgb_residual_pred,
    "Daily_COGS":    # tương tự với COGS model
})
submission.to_csv("submission.csv", index=False)
```

---

## 2. Workflow 2 — Customer Propensity

**Files**: `cust_train.csv` (65 550 rows) · `cust_test.csv` (23 374 rows)  
**Target**: `TARGET_Bought_in_2022` (binary: 0/1)  
**Luôn drop**: `customer_id`, `Total_Spend_In_2022` (data leakage!)

---

### Bước 1 — Feature Engineering

#### 1a. Target Encoding (đã có sẵn trong dataset)

> Các cột `region_enc` và `acquisition_channel_enc` đã được **tính sẵn trên train set** — bạn không cần re-encode. Tuy nhiên nếu muốn tự build pipeline thì:

```python
# Target encoding: thay thế category bằng mean(target) của nhóm đó
# PHẢI fit chỉ trên train set để tránh leakage
from category_encoders import TargetEncoder

enc = TargetEncoder(cols=["region", "acquisition_channel"])
enc.fit(X_train, y_train)
X_train_enc = enc.transform(X_train)
X_test_enc  = enc.transform(X_test)   # dùng encoding đã fit từ train
```

#### 1b. RFM Scaling

```python
from sklearn.preprocessing import RobustScaler

rfm_cols = ["Recency_Days", "Frequency", "Monetary", "Avg_Order_Value"]
scaler = RobustScaler()   # robust hơn StandardScaler khi có whale customers
X_train[rfm_cols] = scaler.fit_transform(X_train[rfm_cols])
X_test[rfm_cols]  = scaler.transform(X_test[rfm_cols])
```

**Tại sao RobustScaler?** Dataset có thể có "whale customers" — những khách hàng với `Monetary` cực kỳ cao. StandardScaler bị kéo lệch bởi outliers; RobustScaler dùng median và IQR nên ổn định hơn.

---

### Bước 2 — Xử lý Class Imbalance

Dataset: Positive rate ≈ **26%** (74% không mua trong 2022).

```python
# Cách 1: scale_pos_weight trong LightGBM
neg_count = (y_train == 0).sum()
pos_count = (y_train == 1).sum()
scale_pos_weight = neg_count / pos_count  # ≈ 2.85

# Cách 2: Stratified K-Fold đảm bảo tỷ lệ đồng đều
from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

---

### Bước 3 — Mô hình LightGBM

**📄 Bài báo gốc**:
> Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). **LightGBM: A Highly Efficient Gradient Boosting Decision Tree**. *Advances in Neural Information Processing Systems 30 (NeurIPS 2017)*, 3146–3154.  
> URL: [https://papers.nips.cc/paper/6907](https://papers.nips.cc/paper/6907)  
> PDF: [https://proceedings.neurips.cc/paper_files/paper/2017/file/6449f44a102fde848669bdd9eb6b76fa-Paper.pdf](https://proceedings.neurips.cc/paper_files/paper/2017/file/6449f44a102fde848669bdd9eb6b76fa-Paper.pdf)

**LightGBM làm gì với dữ liệu khách hàng?**

LightGBM là GBDT với hai kỹ thuật mới:

| Kỹ thuật | Mô tả | Tác động với dataset của bạn |
|---|---|---|
| **GOSS** (Gradient-based One-Side Sampling) | Chỉ giữ các sample có gradient lớn (đang dự báo sai nhiều) | Tập trung học các khách hàng khó phân loại — rất quan trọng với imbalanced data |
| **EFB** (Exclusive Feature Bundling) | Gộp các feature ít khi đồng thời khác 0 | Hiệu quả với one-hot columns: `age_group_*`, `gender_*`, `category_*` |

**Biến ngoại sinh và cách LightGBM xử lý chúng**:

| Nhóm biến | Cột | Ý nghĩa kinh doanh |
|---|---|---|
| **RFM** | `Recency_Days`, `Frequency`, `Monetary`, `Avg_Order_Value` | Hành vi mua hàng lịch sử — signal mạnh nhất |
| **Quality signal** | `Avg_Review_Rating` | Khách hàng hài lòng → khả năng quay lại cao |
| **Return behavior** | `Total_Return_Orders`, `Return_Rate` | Khách hay trả hàng → propensity thấp hơn |
| **Demographics (encoded)** | `region_enc`, `acquisition_channel_enc` | Target encoding giữ nguyên thông tin thống kê |
| **Demographics (one-hot)** | `age_group_*`, `gender_*` | LightGBM xử lý bool features natively, EFB tự bundle chúng |

```python
import lightgbm as lgb
from sklearn.metrics import f1_score, average_precision_score

DROP_CUST = ["TARGET_Bought_in_2022", "customer_id", "Total_Spend_In_2022"]
X_train = cust_train.drop(columns=DROP_CUST)
y_train = cust_train["TARGET_Bought_in_2022"]

params = {
    "objective":        "binary",
    "metric":           ["binary_logloss", "auc"],
    "scale_pos_weight": scale_pos_weight,   # xử lý imbalance
    "learning_rate":    0.05,
    "num_leaves":       63,
    "min_child_samples": 20,
    "random_state":     42,
    "n_jobs":           -1,
}

# Stratified K-Fold cross-validation
f1_scores = []
for fold, (tr_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
    X_tr, X_val = X_train.iloc[tr_idx], X_train.iloc[val_idx]
    y_tr, y_val = y_train.iloc[tr_idx], y_train.iloc[val_idx]
    
    model = lgb.LGBMClassifier(**params, n_estimators=500)
    model.fit(X_tr, y_tr,
              eval_set=[(X_val, y_val)],
              callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)])
    
    y_prob = model.predict_proba(X_val)[:, 1]
    y_pred = (y_prob > 0.5).astype(int)
    f1_scores.append(f1_score(y_val, y_pred))
    print(f"Fold {fold+1} F1: {f1_scores[-1]:.4f}")

print(f"Mean F1: {np.mean(f1_scores):.4f} ± {np.std(f1_scores):.4f}")
```

**Metrics tập trung**:

| Metric | Tại sao quan trọng |
|---|---|
| **F1-Score** | Balance giữa Precision (không waste marketing budget) và Recall (không bỏ sót khách tiềm năng) |
| **PR-AUC** | Tốt hơn ROC-AUC khi class imbalanced — đo trực tiếp trên precision-recall space |

---

### Bước 4 — Feature Importance Analysis

```python
import matplotlib.pyplot as plt

# LightGBM built-in importance
lgb.plot_importance(model, max_num_features=15, importance_type="gain")
plt.title("Feature Importance (Gain)")
plt.tight_layout()
plt.savefig("feature_importance_customer.png")
```

**Kết quả kỳ vọng**:

| Rank | Feature | Lý do quan trọng |
|---|---|---|
| 1 | `Recency_Days` | Khách mua gần đây → signal mạnh nhất về intention |
| 2 | `Monetary` | Khách chi nhiều → loyal customer |
| 3 | `Frequency` | Mua nhiều lần → habit formation |
| 4 | `Avg_Review_Rating` | Satisfaction → retention |
| 5 | `Return_Rate` | Negative signal |

---

## 3. Workflow 3 — Product Inventory Risk

**File**: `ml_product_inventory.csv` (1 624 SKU · 17 cols)  
**Target**: `TARGET_Stockout_Risk_30d` (binary: 0/1, positive rate ≈ **0.3%**)  
**Drop**: `product_id`  
**Dùng file đầy đủ** — `product_train.csv` (legacy) thiếu cột `GMROI` và `n_months`

---

### Bước 1 — Xây dựng Ma trận Đặc trưng

**Biến ngoại sinh quan trọng nhất**:

| Nhóm | Cột | Giải thích |
|---|---|---|
| **Inventory state** | `stock_on_hand`, `avg_stock_on_hand`, `avg_stockout_days`, `avg_fill_rate` | Snapshot tồn kho hiện tại và lịch sử |
| **Demand velocity** | `Daily_Velocity`, `avg_monthly_units_sold`, `avg_sell_through` | Tốc độ tiêu thụ — key driver của stockout |
| **Profitability** | `GMROI`, `Gross_Margin_Pct`, `price`, `cogs` | Sản phẩm margin cao → ưu tiên re-stock |
| **History depth** | `n_months` | Bao nhiêu tháng dữ liệu → độ tin cậy của estimates |
| **Category** | `category_GenZ`, `category_Outdoor`, `category_Streetwear` | Tính mùa vụ theo danh mục |

**GMROI formula** (đã có trong dataset):
```
Avg_Inventory_Cost = mean(stock_on_hand) × cogs
Annualized_Revenue = avg_monthly_units_sold × price × 12
GMROI = (Annualized_Revenue × Gross_Margin_Pct) / Avg_Inventory_Cost
```

---

### Bước 2 — Random Forest Classifier

**📄 Bài báo gốc**:
> Breiman, L. (2001). **Random Forests**. *Machine Learning*, 45(1), 5–32.  
> DOI: [10.1023/A:1010933404324](https://doi.org/10.1023/A:1010933404324)

**Random Forest làm gì với dữ liệu tồn kho?**

Random Forest xây dựng nhiều cây quyết định độc lập (bootstrap samples + random feature subsets), sau đó vote majority:

| Ưu điểm với bài toán này | Lý do |
|---|---|
| Ổn định với dataset nhỏ (~1 600 SKU) | Không cần nhiều data như Deep Learning |
| Tự nhiên xử lý feature interactions | `Daily_Velocity` × `stock_on_hand` interaction được học tự động |
| Robust với outliers | Bootstrap sampling giảm ảnh hưởng của outlier SKUs |
| OOB error estimate | Validation miễn phí từ out-of-bag samples |

**Xử lý extreme imbalance (positive rate ≈ 0.3%)**:

```python
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

DROP_PROD = ["TARGET_Stockout_Risk_30d", "product_id"]
X = prod.drop(columns=DROP_PROD)
y = prod["TARGET_Stockout_Risk_30d"]

# SMOTE trước khi train
smote = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote.fit_resample(X, y)

# class_weight bổ sung
model_rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_leaf=2,
    class_weight={0: 1, 1: 300},   # positive rate ≈ 0.3% → weight ≈ 300
    random_state=42,
    n_jobs=-1,
    oob_score=True
)
model_rf.fit(X_resampled, y_resampled)
print(f"OOB Score: {model_rf.oob_score_:.4f}")
```

---

### Bước 3 — SHAP Values (Explainable AI)

**📄 Bài báo gốc**:
> Lundberg, S. M., & Lee, S.-I. (2017). **A Unified Approach to Interpreting Model Predictions**. *Advances in Neural Information Processing Systems 30 (NeurIPS 2017)*, 4765–4774.  
> URL: [https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html)  
> arXiv: [https://arxiv.org/abs/1705.07874](https://arxiv.org/abs/1705.07874)

**SHAP làm gì?**

SHAP tính contribution của từng feature cho **từng dự báo riêng lẻ** dựa trên lý thuyết Shapley values từ cooperative game theory:

```
prediction = base_value + SHAP(feature_1) + SHAP(feature_2) + ... + SHAP(feature_n)
```

```python
import shap

explainer  = shap.TreeExplainer(model_rf)
shap_values = explainer.shap_values(X)  # shape: (n_samples, n_features)

# Summary plot — feature importance toàn cục
shap.summary_plot(shap_values[1], X, plot_type="bar",
                  feature_names=X.columns.tolist())

# Force plot — giải thích SKU cụ thể
sku_idx = 42  # ví dụ: SKU bị cảnh báo
shap.force_plot(
    explainer.expected_value[1],
    shap_values[1][sku_idx],
    X.iloc[sku_idx],
    feature_names=X.columns.tolist()
)
```

**Insight mẫu từ SHAP**:

```
SKU #1024 bị cảnh báo Stockout Risk = 1
├── stock_on_hand = 45 units           SHAP = -0.12  (tồn kho còn khá ổn)
├── Daily_Velocity = 8.3 units/day     SHAP = +0.34  ← DRIVER CHÍNH (tốc độ cao)
├── avg_stockout_days = 3.2 days/month SHAP = +0.18  (lịch sử hay hết hàng)
├── GMROI = 4.7                        SHAP = +0.08  (sản phẩm sinh lời tốt)
└── category_Streetwear = True         SHAP = +0.11  (mùa vụ cao)

→ Kết luận: Không phải tồn kho thấp, mà do velocity tăng đột biến + lịch sử stockout
```

---

### Bước 4 — Output: Danh sách SKU cần nhập hàng

```python
# Lấy threshold tối ưu từ precision-recall curve
from sklearn.metrics import precision_recall_curve

y_prob = model_rf.predict_proba(X)[:, 1]
precision, recall, thresholds = precision_recall_curve(y, y_prob)
# Chọn threshold với F1 cao nhất
f1_scores = 2 * precision * recall / (precision + recall + 1e-9)
optimal_threshold = thresholds[np.argmax(f1_scores)]

# Xuất danh sách
prod["Stockout_Risk_Prob"] = y_prob
prod["Stockout_Alert"]     = (y_prob >= optimal_threshold).astype(int)

restock_list = (
    prod[prod["Stockout_Alert"] == 1]
    [["product_id", "Stockout_Risk_Prob", "stock_on_hand",
      "Daily_Velocity", "GMROI"]]
    .sort_values("Stockout_Risk_Prob", ascending=False)
)
restock_list.to_csv("restock_priority_list.csv", index=False)
print(f"Số SKU cần nhập hàng: {len(restock_list)}")
```

---

## 4. Tài liệu tham khảo

### Papers chính

| # | Tên bài báo | Tác giả | Năm | Venue | Link |
|---|---|---|---|---|---|
| 1 | **Forecasting at Scale** (Prophet) | Taylor & Letham | 2018 | *The American Statistician* | [DOI](https://doi.org/10.1080/00031305.2017.1380080) · [arXiv](https://arxiv.org/abs/1701.09209) |
| 2 | **XGBoost: A Scalable Tree Boosting System** | Chen & Guestrin | 2016 | *KDD 2016* | [DOI](https://doi.org/10.1145/2939672.2939785) · [arXiv](https://arxiv.org/abs/1603.02754) |
| 3 | **LightGBM: A Highly Efficient Gradient Boosting Decision Tree** | Ke et al. | 2017 | *NeurIPS 2017* | [Proceedings](https://papers.nips.cc/paper/6907) · [PDF](https://proceedings.neurips.cc/paper_files/paper/2017/file/6449f44a102fde848669bdd9eb6b76fa-Paper.pdf) |
| 4 | **Random Forests** | Breiman | 2001 | *Machine Learning* | [DOI](https://doi.org/10.1023/A:1010933404324) |
| 5 | **A Unified Approach to Interpreting Model Predictions** (SHAP) | Lundberg & Lee | 2017 | *NeurIPS 2017* | [Proceedings](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html) · [arXiv](https://arxiv.org/abs/1705.07874) |
| 6 | **Optuna: A Next-generation Hyperparameter Optimization Framework** | Akiba et al. | 2019 | *KDD 2019* | [DOI](https://doi.org/10.1145/3292500.3330701) · [arXiv](https://arxiv.org/abs/1907.10902) |

### Đọc thêm (tùy chọn)

| Chủ đề | Tài liệu |
|---|---|
| NeuralProphet (Prophet + AR) | Triebe et al. (2021) — [arXiv:2111.15397](https://arxiv.org/abs/2111.15397) |
| SMOTE (oversampling) | Chawla et al. (2002), *JAIR* — [arXiv:1106.1813](https://arxiv.org/abs/1106.1813) |
| RobustScaler lý thuyết | Huber (1981), *Robust Statistics*, Wiley |
| Expanding Window CV | Hyndman & Athanasopoulos (2021), *Forecasting: Principles and Practice* — [otexts.com/fpp3](https://otexts.com/fpp3) |

---

## Checklist trước khi submit

```
□ random_state=42 ở mọi bước (RandomForest, LightGBM, XGBoost, SMOTE, train_test_split)
□ Drop order_date TRƯỚC khi đưa vào XGBoost .fit()
□ Drop Total_Spend_In_2022 TRƯỚC khi train customer model
□ Target encoding fit CHỈ trên cust_train, transform cả train và test
□ RobustScaler fit CHỈ trên train, transform cả train và test
□ Dùng ml_product_inventory.csv (17 cols) thay vì product_train.csv (14 cols) để có GMROI
□ Expanding Window CV — KHÔNG dùng random K-Fold cho time series
□ SHAP analysis cho ít nhất 1 SKU cụ thể trong phần báo cáo
□ submission.csv có đúng 184 rows (2022-07-01 → 2022-12-31)
```
