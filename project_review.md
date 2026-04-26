# 🏆 Datathon 2026 — Đánh Giá Trạng Thái Project (Nhóm GGB)

> **Cuộc thi:** DATATHON 2026 — The Gridbreakers | VinTelligence — VinUni DS&AI Club  
> **Chủ đề:** Tối ưu hóa Hệ sinh thái Thương mại Điện tử (Thời trang)  
> **Dữ liệu:** 14 file CSV, 2012–2024  
> **Ngày review:** 21/04/2026

---

## 📊 Tổng Quan Điểm Thi (Reminder)

| Phần | Nội dung | Điểm | Tỷ trọng |
|------|----------|------|----------|
| 1 | Câu hỏi Trắc nghiệm (10 câu × 2đ) | 20 | 20% |
| 2 | Trực quan hoá & Phân tích EDA | 60 | **60%** |
| 3 | Mô hình Dự báo Doanh thu (MAE/RMSE/R²) | 20 | 20% |

> **EDA chiếm 60% tổng điểm** — đây là trọng tâm chiến lược cần đầu tư lớn nhất.

---

## ✅ PHẦN 1 — NHỮNG GÌ PROJECT ĐÃ LÀM TỐT

### 🔧 1.1 Data Pipeline (`data_pipeline.py`) — Kiến trúc Xuất sắc

**Thiết kế ETL 4 Stage chuẩn production:**
- **Stage 1 (Load):** Tự động cast date columns, graceful skip nếu file thiếu, log rõ ràng từng file với layer label
- **Stage 2 (Clean):** Business-rule validation đúng chuẩn — drop `cogs >= price`, retain hợp lệ order_status, drop orphan reviews
- **Stage 3 (Merge):** Star Schema join strategy với tư duy rõ ràng — pre-aggregate returns để tránh fan-out trước khi join, LEFT JOIN nhất quán
- **Stage 4 (Analytical):** Daily aggregation với feature engineering hoàn chỉnh — calendar features, `is_holiday` dùng cả spike detection + VN public holidays library, `is_promo`, web traffic, inventory monthly merge

**Điểm nổi bật về tính chính xác:**
- ✅ Refund được deduct đúng trên `return_date`, KHÔNG phải `order_date` — tránh corrupt lịch sử Revenue
- ✅ Inventory join có guard assertion chống fan-out (runtime check row count không đổi)
- ✅ MAPE benchmark so với `sales.csv` reference được tính ngay trong pipeline
- ✅ Reviews join được aggregate về order-level trước khi merge
- ✅ Geometric mean YoY growth rate được tính đúng công thức

### 📓 1.2 EDA Notebook (`Phase_1.ipynb`) — Nền tảng Tốt

**Những gì notebook đã thực hiện:**
- ✅ Load và profile đủ 14 tables với shape, dtype, date range
- ✅ Tự build master dataset trong notebook (714,669 rows × 62 cols) — bao gồm cả dual-promo join (p1 + p2) đúng logic
- ✅ FK Integrity Evaluation đánh giá **15 relationships**, kết quả: 0 orphans, 0 errors
- ✅ Data cleaning với audit log đầy đủ (log từng action, rows affected)
- ✅ Business metrics đã được tính: Revenue, COGS, Profit, gross_margin
- ✅ Time-series features đã được engineer: year, month, day_of_week, quarter
- ✅ Recognized missing values có nghĩa (ship_date/delivery_date null = chưa ship)
- ✅ `size` được cast thành ordered categorical (S < M < L < XL) — đúng

### 🗂️ 1.3 Data Coverage

- ✅ Có đủ 14/14 file CSV được referencing (trừ `inventory_enhanced` chưa tồn tại — đây là file bổ sung tự tạo)
- ✅ `master_dataset.csv` đã được generate và lưu ra (daily analytical file)
- ✅ `sample_submission.csv` đã có sẵn để tham chiếu format nộp bài

---

## ❌ PHẦN 2 — NHỮNG VẤN ĐỀ CẦN PHẢI SỬA

### 🚨 2.1 Lỗi Nghiêm Trọng — Bất Nhất Giữa Pipeline và Notebook

> **ĐÂY LÀ VẤN ĐỀ LỚN NHẤT.**

`data_pipeline.py` và `Phase_1.ipynb` **build master dataset theo 2 cách khác nhau**:

| Điểm khác biệt | `data_pipeline.py` | `Phase_1.ipynb` (Cell 3) |
|---|---|---|
| Spine | `order_items` | `order_items` ✅ |
| Promotions join | join qua `promotions` table với `start_date`/`end_date` | Join trực tiếp `promo_id` từ `order_items` (p1 + p2) |
| Returns | Pre-aggregate `(order_id, product_id)` | Không thấy rõ trong cells |
| Reviews | Aggregate rồi left join | Có cell nhưng cell 9 trống |
| Output | Daily aggregate file | Item-level fact table (714,669 rows × 62 cols) |
| `Net_Revenue` | `quantity × unit_price - discount_amount` | `Revenue` = `quantity × unit_price - discount_amount` (column name khác!) |

→ **Phải thống nhất một source of truth duy nhất.** Notebook nên import và gọi `data_pipeline.py`, không tự build lại.

### ⚠️ 2.2 EDA Còn Dừng Ở Mức Descriptive/Diagnostic — Thiếu Prescriptive

Nhìn vào rubric chấm điểm (60đ):

| Tiêu chí | Điểm max | Trạng thái hiện tại |
|---|---|---|
| Chất lượng trực quan hoá | 15đ | ⚠️ Notebook mới có 1 figure (6-chart EDA suite) chưa rendered đủ |
| Chiều sâu phân tích | 25đ | ⚠️ Mới Descriptive + sơ bộ Diagnostic, **thiếu Predictive và Prescriptive** |
| Insight kinh doanh | 15đ | ❌ Chưa có business recommendations cụ thể với số liệu |
| Tính sáng tạo & kể chuyện | 5đ | ❌ Chưa có narrative structure, insight rải rác trong code |

**Bốn cấp độ phân tích cần đạt:**
- **Descriptive** ✅ (đã có stats, charts cơ bản)
- **Diagnostic** ⚠️ (mới bắt đầu — có FK check, có cleaning, chưa đủ "Why did this happen?")
- **Predictive** ❌ (chưa có seasonality analysis, trend decomposition, lead indicator analysis)
- **Prescriptive** ❌ (chưa có business recommendations với trade-off định lượng)

### ⚠️ 2.3 Các Lỗi Kỹ Thuật Cụ Thể Trong Notebook

1. **Cell 4:** Tính `Revenue` nhưng không sử dụng đúng formula từ đề thi với promotions:
   - Đề thi: `percentage → discount = qty × price × (discount_value/100)`, `fixed → discount = qty × discount_value`
   - Notebook đang dùng `discount_amount` từ `order_items` trực tiếp — cần verify xem con số này đã pre-calculated chưa

2. **Cell 5:** Chart 1 dùng `Net_Revenue` nhưng column này được tạo trong `data_pipeline.py`, **không tồn tại** trong notebook's master dataset (notebook tạo column tên `Revenue`) → **KeyError sẽ xảy ra**

3. **Cell 9:** Hoàn toàn trống — pipeline trong notebook bị bỏ dở

4. **Thiếu output rendering:** Nhiều cells có `[OUT]` trống hoặc truncated, không biết charts đã render đúng chưa

5. **Missing: 10 câu MCQ chưa được trả lời** trong notebook — các câu này yêu cầu tính toán trực tiếp từ data:
   - Q1: Median inter-order gap của repeat customers
   - Q2: Segment có gross margin cao nhất `(price-cogs)/price`
   - Q3: Return reason phổ biến nhất của Streetwear
   - Q4: Traffic source có bounce_rate thấp nhất
   - Q5: % order_items có promo_id
   - Q6: Age group có avg orders/customer cao nhất
   - Q7: Region có tổng doanh thu cao nhất trong sales_train
   - Q8: Payment method của cancelled orders
   - Q9: Size có tỷ lệ return cao nhất
   - Q10: Installment plan có avg payment value cao nhất

### ⚠️ 2.4 Phần Forecasting (Phần 3) — Chưa Bắt Đầu

- ❌ Chưa có model training code (Prophet / XGBoost như thiết kế ban đầu)
- ❌ Chưa có `submission.csv` để nộp Kaggle
- ❌ Chưa có time-series cross-validation (TimeSeriesSplit — bắt buộc để tránh leakage)
- ❌ Chưa có SHAP values / feature importance explanation
- ❌ Chưa có anti-leakage check: không được dùng `Revenue`/`COGS` từ test set làm feature

### ⚠️ 2.5 Submission Requirements Chưa Đáp Ứng

- ❌ Báo cáo LaTeX theo template NeurIPS (tối đa 4 trang) — chưa có
- ❌ Link Kaggle submission — chưa nộp
- ❌ GitHub repo cần public với README hướng dẫn reproduce — chưa hoàn chỉnh

---

## 🚀 PHẦN 3 — LỘ TRÌNH BƯỚC ĐI TIẾP THEO

### 📌 Priority Matrix

| Task | Điểm tác động | Độ khó | Priority |
|---|---|---|---|
| Trả lời 10 câu MCQ | 20đ | Thấp | 🔴 **NGAY BÂY GIỜ** |
| EDA Prescriptive Level | 25đ (chiều sâu) | Trung bình | 🔴 **NGAY BÂY GIỜ** |
| Business Insights + Viz | 30đ (viz+insight) | Trung bình | 🔴 **NGAY BÂY GIỜ** |
| Baseline Forecasting Model | 20đ | Trung bình | 🟠 **SỚM** |
| NeurIPS Report LaTeX | Tất cả | Cao | 🟠 **SỚM** |
| SHAP + Model Explanation | 8đ (báo cáo kỹ thuật) | Cao | 🟡 Sau |

---

### BƯỚC 1 — Sửa Ngay (1-2 ngày) 🔴

#### 1a. Trả Lời 10 Câu MCQ
Tạo một notebook riêng `mcq_answers.ipynb`:
```python
# Q1: Median inter-order gap
orders_sorted = orders.sort_values(['customer_id', 'order_date'])
gaps = orders_sorted.groupby('customer_id')['order_date'].diff().dt.days
repeat_customers = orders.groupby('customer_id').size()
repeat_customers = repeat_customers[repeat_customers > 1].index
median_gap = gaps[orders_sorted['customer_id'].isin(repeat_customers)].median()
# → Đáp án kỳ vọng: C) 144 ngày

# Q2: Gross margin by segment
products['gross_margin'] = (products['price'] - products['cogs']) / products['price']
products.groupby('segment')['gross_margin'].mean().sort_values(ascending=False)

# Q5: % order_items có promo_id
pct_promo = order_items['promo_id'].notna().mean() * 100
# → Kỳ vọng: C) 39%
```

#### 1b. Thống Nhất Master Dataset
- Xóa code build dataset trong notebook, thay bằng:
```python
from data_pipeline import load_data, clean_data, merge_tables, create_analytical_file
dfs = load_data()
dfs = clean_data(dfs)
master_fact = merge_tables(dfs)  # item-level
daily_df = create_analytical_file(master_fact, ...)  # daily
```
- Đảm bảo column names nhất quán: `Net_Revenue`, `COGS_Line`, `Actual_Profit`

---

### BƯỚC 2 — EDA Prescriptive (3-5 ngày) 🔴

Tổ chức notebook theo **4 cấp độ phân tích**:

#### 📊 Level 1 — Descriptive ("What happened?")
- Revenue trend 2012–2022 với rolling average
- Revenue breakdown: by category, segment, region, device_type
- Order volume heatmap: day_of_week × month
- Customer demographics: gender, age_group pie charts
- Top 10 products by revenue và return rate

#### 🔍 Level 2 — Diagnostic ("Why did it happen?")
- **Return rate analysis:** Streetwear vs others, size XL hypothesis test
- **Cancellation analysis:** Cancelled orders vs payment method, time of day
- **Seasonality decomposition:** STL decomposition để isolate trend/seasonal/residual
- **Cohort analysis:** Retention rate by signup_year
- **Promo impact:** Revenue lift on `is_promo=1` days vs baseline

#### 🔮 Level 3 — Predictive ("What is likely to happen?")
- YoY growth rate extrapolation với confidence interval
- Tết seasonality pattern: day -30 đến day +7 xung quanh Tết mỗi năm
- Web traffic → Revenue correlation (lag analysis: traffic leads revenue by N days?)
- Inventory stockout → Revenue loss estimation
- Return rate trend: đang tăng hay giảm qua các năm?

#### 💡 Level 4 — Prescriptive ("What should we do?")
Cần có **số liệu cụ thể** với mỗi đề xuất:

| Phát hiện | Hành động đề xuất | ROI ước tính |
|---|---|---|
| XL có return rate cao nhất | Cải thiện size guide, thêm review cho XL | Giảm N% return cost |
| Tết spike revenue 3x | Tăng inventory 200% trước Tết 3 tuần | +X triệu VNĐ |
| Email campaign bounce_rate thấp nhất | Tăng budget email vs social | +Y% conversion |
| Streetwear return vì wrong_size | Thêm size recommendation AI | Giảm Z% return |

---

### BƯỚC 3 — Forecasting Model (3-4 ngày) 🟠

#### Thiết Kế Pipeline Không Leakage:
```python
# Train: sales.csv → 2012-07-04 đến 2022-12-31
# Test:  sample_submission.csv → 2023-01-01 đến 2024-07-01

# Features từ master_dataset (KHÔNG có Revenue/COGS từ tương lai):
features = [
    'year', 'month', 'day', 'day_of_week', 'quarter', 'is_weekend',
    'is_holiday', 'is_promo',
    'sessions', 'unique_visitors', 'bounce_rate',  # web_traffic
    'inv_stock_on_hand', 'inv_sell_through_rate',   # inventory
    'yoy_growth_ref'                                 # trend
]

# Cross-validation đúng chiều thời gian:
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5, gap=30)  # gap=30 ngày tránh look-ahead
```

#### Model Strategy:
1. **Baseline:** Seasonal Mean (đã có trong `baseline.ipynb`)
2. **Model 1:** Prophet (trend + seasonality tự động)
3. **Model 2:** XGBoost với time-series features
4. **Ensemble:** Weighted average Prophet + XGBoost → submit

#### SHAP Explanation (bắt buộc cho 8đ báo cáo kỹ thuật):
```python
import shap
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test)
# → Identify: is_holiday, is_promo, month là top drivers
```

---

### BƯỚC 4 — NeurIPS Report LaTeX (2 ngày) 🟠

**Cấu trúc 4 trang:**

```
Trang 1: Abstract + Introduction + Data Summary table
Trang 2: EDA Highlights — 4-6 key charts với captions
Trang 3: Forecasting Methodology + Results table (MAE/RMSE/R²)
Trang 4: Business Recommendations + Feature Importance (SHAP plot)
```

**Bắt buộc include:**
- Bảng data schema với table count và row count
- Feature engineering decisions và rationale
- Cross-validation methodology để chứng minh không leakage
- Business language explanation của model findings

---

### BƯỚC 5 — Submission Checklist 🟡

- [ ] Nộp `submission.csv` lên Kaggle, kiểm tra đúng thứ tự như `sample_submission.csv`
- [ ] Compile report PDF từ LaTeX template NeurIPS
- [ ] GitHub repo: public, có README với instructions reproduce
- [ ] Form nộp bài: chọn MCQ answers, upload PDF, link Kaggle, link GitHub
- [ ] Ảnh thẻ sinh viên của tất cả thành viên
- [ ] Xác nhận có thành viên tham dự trực tiếp ngày 23/05/2026 tại VinUni, Hà Nội

---

## 🎯 Tóm Tắt Executive Summary

| Hạng mục | Trạng thái | Điểm rủi ro |
|---|---|---|
| Data Pipeline | ✅ Xuất sắc | Thấp |
| Data Cleaning & FK Check | ✅ Tốt | Thấp |
| Descriptive EDA | ⚠️ Chưa đủ charts | Trung bình |
| Diagnostic EDA | ⚠️ Mới bắt đầu | **Cao** |
| Predictive/Prescriptive EDA | ❌ Chưa có | **Rất cao** |
| MCQ (10 câu) | ❌ Chưa trả lời | **Cao – dễ lấy điểm** |
| Forecasting Model | ❌ Chưa có | **Cao** |
| Submission | ❌ Chưa nộp Kaggle | **Critical** |
| Report LaTeX | ❌ Chưa có | **Critical** |

> **Ưu tiên tuyệt đối:** MCQ → EDA Prescriptive → Forecasting → Report → Submit
> 
> Nền tảng kỹ thuật (pipeline, data quality) của project **rất tốt** — đây là lợi thế cạnh tranh lớn. Vấn đề là phần "storytelling" và model chưa được build. Tập trung vào output thay vì infrastructure trong giai đoạn còn lại.
