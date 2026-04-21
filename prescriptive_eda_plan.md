# 🎯 Prescriptive EDA Plan — Datathon 2026

**Role:** Senior Data Scientist + Business Domain Knowledge  
**Audience:** Kinh tế team → Stakeholders (không cần biết code)  
**North Star:** Mỗi phân tích kết thúc bằng **hành động cụ thể + ROI ước tính**

> Đọc từng ô bên dưới, phản hồi ✅ GIỮ / ❌ BỎ / ⚠️ SỬA trước khi implement.

---

## 🧭 Nguyên tắc — Prescriptive ≠ "Vẽ thêm chart đẹp"

```
Descriptive  → "Doanh thu tháng 1 tăng 30%"
Diagnostic   → "Vì Tết Nguyên Đán — traffic tăng 5x"
Predictive   → "Năm tới tháng 1-2 sẽ tăng ~25-35%"
Prescriptive → "→ NẠP KHO thêm 40% top-3 danh mục trước 20/12,
                   dự kiến +15M revenue, tránh stockout 8 ngày"
```

**Mỗi subtask phải trả lời: "So, what should we DO?" + số tiền hoặc % cụ thể**

---

## 🪟 WINDOW 1 — Promotion ROI: Khuyến Mãi Nào Thực Sự Có Lời?

**📌 Câu hỏi kinh doanh:**
> "Chúng ta đang chạy khuyến mãi đúng hay chỉ đang tặng tiền?"

**🎯 Mục tiêu:**
Đo **revenue lift thực sự** của từng loại promo (percentage vs fixed discount),
so sánh với baseline (ngày không có promo). Tính gross margin còn lại sau discount.

**📊 Data sử dụng:**
- `order_items` — promo_id, discount_amount, quantity, unit_price
- `promotions` — promo_type, discount_value, start_date, end_date, applicable_category
- `daily_df` / pipeline — is_promo column, daily Revenue

**📈 Output kỳ vọng (stakeholder table):**

| Promotion Type | Revenue/ngày | Margin còn lại | Lift vs baseline |
|---------------|-------------|----------------|-----------------|
| Flash Sale (%) | X triệu     | Y%             | +Z%             |
| Fixed Discount | ...         | ...            | ...             |
| Bundling       | ...         | ...            | ...             |
| Không promo    | baseline    | baseline%      | —               |

**💡 Prescriptive Output:**
> "Flash Sale 30% đang ăn hết margin — chỉ nên chạy cho hàng tồn kho >60 ngày.  
> Fixed discount 50k VNĐ có incremental +18% revenue mà margin vẫn dương.  
> **Đề xuất: Chuyển 70% budget promo sang Fixed Discount, dừng % discount cho Premium segment.**"

**⚙️ Độ phức tạp:** ⭐⭐ Trung bình | **⏱️ Ước tính:** 3–4 giờ  
**🎯 Điểm thi:** Diagnostic (25đ chiều sâu) + Insight kinh doanh (15đ)

---

## 🪟 WINDOW 2 — Return Rate Deep-Dive: Ai Trả Hàng, Tại Sao?

**📌 Câu hỏi kinh doanh:**
> "Return cost đang bào mòn profit bao nhiêu? Có thể ngăn được không?"

**🎯 Mục tiêu:**
Xác định **chuỗi nhân quả** của return: product dimension → customer segment → return reason.
Tính **tổng chi phí ẩn** = refund + logistics + lost margin.

**📊 Data sử dụng:**
- `returns` — return_reason, return_quantity, refund_amount
- `order_items` + `products` — category, segment, size
- `customers` — age_group, gender

**📈 Output kỳ vọng:**
```
Return Cost Breakdown (top 3 nguyên nhân):
  Streetwear + Size XL  → wrong_size    → 32% tổng return cost
  Premium + Female 25-34 → changed_mind → 18% tổng return cost
  Activewear            → defective     → 12% tổng return cost

Counterfactual: Giảm wrong_size 50% → tiết kiệm X triệu VNĐ/năm
```

**💡 Prescriptive Output:**
> "**Action 1:** Thêm size guide interactive + pin customer reviews cho Streetwear XL  
> **Action 2:** '14-day try-on' policy cho Premium → giảm changed_mind, tăng trust  
> **ROI ước tính:** Giảm return rate 8 percentage points → +X triệu margin/năm"

**⚙️ Độ phức tạp:** ⭐⭐ Trung bình | **⏱️ Ước tính:** 3–4 giờ  
**🎯 Điểm thi:** Cao — multi-table, số liệu cụ thể, actionable recommendation

---

## 🪟 WINDOW 3 — Customer Segmentation (RFM): Ai Là Khách Hàng Vàng?

**📌 Câu hỏi kinh doanh:**
> "Trong 600k+ khách, chúng ta nên giữ chân ai? Và bỏ qua ai để tiết kiệm cost?"

**🎯 Mục tiêu:**
RFM Segmentation (Recency × Frequency × Monetary) → 4 nhóm hành động:
- **Champions** — mua gần, mua nhiều, chi nhiều
- **At-Risk** — từng là Champions, đang im lặng
- **New Customers** — mới mua lần đầu (<90 ngày)
- **Lost** — không mua >365 ngày

**📊 Data sử dụng:**
- `orders` — order_date, customer_id, order_status
- `order_items` — quantity, unit_price, discount_amount  
- `customers` — age_group, acquisition_channel, signup_date

**📈 Output kỳ vọng (executive summary table):**

```
Segment          | Số KH    | % Revenue | Avg LTV    | Action
Champions        | ~12,400  | 47%       | 8.2M VNĐ  | Loyalty program
At-Risk          | ~28,000  | 31%       | 3.1M VNĐ  | Win-back email 10% off
New (<90 ngày)   | ~45,000  | 15%       | 0.8M VNĐ  | Onboarding promo
Lost (>365 ngày) | ~120,000 | 7%        | 0.2M VNĐ  | Low-cost SMS / Bỏ qua
```

**💡 Prescriptive Output:**
> "**Tập trung 80% marketing budget vào Champions + At-Risk** (40k KH = 78% revenue).  
> Win-back At-Risk: email 10% off → nếu 20% quay lại = +Y triệu incremental.  
> **Đừng** invest marketing vào 120k Lost customers — ROI âm."

**⚙️ Độ phức tạp:** ⭐⭐⭐ Trung bình-Cao | **⏱️ Ước tính:** 4–5 giờ  
**🎯 Điểm thi:** Rất cao — creativity, cross-table, CLV calculation

---

## 🪟 WINDOW 4 — Seasonal Demand Planning: Nạp Kho Khi Nào, Bao Nhiêu?

**📌 Câu hỏi kinh doanh:**
> "Chúng ta hay bị stockout vào mùa cao điểm — phải chuẩn bị trước bao nhiêu ngày?"

**🎯 Mục tiêu:**
Kết hợp **10 năm seasonality pattern** (sales.csv) với **inventory data**:
- Monthly Seasonal Index cho từng category
- Lead time tối ưu cần nạp kho
- Ước tính revenue lost do stockout

**📊 Data sử dụng:**
- `sales.csv` — Revenue time series 2012–2022 (10 năm)
- `inventory` — stock_on_hand, units_sold, stockout_days, days_of_supply, fill_rate
- `products` — category, segment

**📈 Output kỳ vọng:**

```
Seasonal Index by Month (avg 10 năm):
  Tháng 1 (Tết Nguyên Đán): 2.8x baseline  ← đỉnh cao nhất
  Tháng 11 (11.11 Sale):    1.9x baseline
  Tháng 7–8 (off-season):   0.7x baseline  ← đáy

Stockout impact:
  Streetwear tháng 1: avg 8 stockout_days → Lost revenue ≈ Z triệu
  
Recommendation chart (Gantt-style):
  Streetwear: Nạp thêm +180% trước 20/12 (lead time 3 tuần)
  Activewear: Nạp thêm +120% trước 01/11
```

**💡 Prescriptive Output:**
> "**Lịch nạp kho 2025:** Streetwear +180% order trước 20/12; Activewear +120% trước 01/11.  
> Giảm tồn kho tháng 7–8 xuống 60% để tiết kiệm warehouse cost.  
> **ROI:** Tránh 8 ngày stockout tháng Tết = +A triệu; giảm overstocking = tiết kiệm B triệu/năm."

**⚙️ Độ phức tạp:** ⭐⭐⭐ Cao (cần STL decomposition) | **⏱️ Ước tính:** 4–5 giờ  
**🎯 Điểm thi:** Cao — liên kết inventory + sales + seasonality (Predictive + Prescriptive)

---

## 🪟 WINDOW 5 — Marketing Channel ROI: Kênh Nào Mang Khách Tốt Nhất?

**📌 Câu hỏi kinh doanh:**
> "Email campaign, social media, paid search — kênh nào hiệu quả trên mỗi đồng chi phí?"

**🎯 Mục tiêu:**
So sánh chất lượng khách hàng (không chỉ volume) theo nguồn traffic:
- Bounce rate thấp = khách có intent cao → chuyển đổi tốt hơn
- Customer LTV theo acquisition_channel
- Revenue per session theo traffic_source

**📊 Data sử dụng:**
- `web_traffic` — traffic_source, sessions, bounce_rate, conversion_rate
- `customers` — acquisition_channel
- Master dataset — Revenue aggregated by customer

**📈 Output kỳ vọng:**

```
Channel         | Sessions | Bounce | Conv.% | Avg LTV  | Quality
email_campaign  | 50K      | 22%    | 4.2%   | 5.1M VNĐ | ⭐⭐⭐⭐⭐ HIGH
organic_search  | 300K     | 35%    | 2.8%   | 3.8M VNĐ | ⭐⭐⭐⭐  MEDIUM
paid_search     | 180K     | 41%    | 2.1%   | 2.9M VNĐ | ⭐⭐⭐   LOW-MED
social_media    | 250K     | 58%    | 0.9%   | 1.2M VNĐ | ⭐       LOW
```

**💡 Prescriptive Output:**
> "Email có LTV cao nhất nhưng volume thấp — **mở rộng email list là priority số 1**.  
> Social media bounce_rate 58% → đang lãng phí budget.  
> **Budget reallocation:** Email +30%, Organic SEO +20%, Paid Search -20%, Social -30%."

**⚙️ Độ phức tạp:** ⭐⭐ Trung bình | **⏱️ Ước tính:** 2–3 giờ  
**🎯 Điểm thi:** Trung bình — creativity, web_traffic + customers join

---

## 🪟 WINDOW 6 — Logistics & SLA: Giao Hàng Chậm Đang Giết Chết Review Score?

**📌 Câu hỏi kinh doanh:**
> "Giao hàng trễ ảnh hưởng đến review và return như thế nào? Con số là bao nhiêu?"

**🎯 Mục tiêu:**
Quantify chuỗi nhân quả: **Delivery delay → Rating drop → Return↑ → Revenue loss**

**📊 Data sử dụng:**
- `shipments` — ship_date, delivery_date, shipping_fee
- `orders` — order_date, order_status, zip
- `reviews` — rating
- `returns` — return_reason
- `geography` — region

**📈 Output kỳ vọng:**

```
Delivery time buckets:
  On-time (<5 ngày):    avg rating = 4.3,  return_rate = 8%
  Late (5–10 ngày):     avg rating = 3.1,  return_rate = 14%  (+75%)
  Very late (>10 ngày): avg rating = 2.1,  return_rate = 23%  (+188%)

Worst region: Central — 34% đơn vi phạm SLA, avg rating = 2.4

Regression estimate: +1 ngày trễ → rating -0.4 → return rate +3% → -X triệu revenue
```

**💡 Prescriptive Output:**
> "**Priority fix: SLA enforcement cho Central** — 34% đơn vi phạm, avg rating 2.4.  
> Thêm 'free express shipping' cho đơn >500k VNĐ → giảm late delivery ~40%.  
> **ROI:** Giảm late delivery 50% → avg rating +0.8 → return rate -6% = +Y triệu/năm."

**⚙️ Độ phức tạp:** ⭐⭐ Trung bình | **⏱️ Ước tính:** 3–4 giờ  
**🎯 Điểm thi:** Cao — cross-table narrative, "connecting data purposefully" (creativity 5đ)

---

## 🪟 WINDOW 7 — Product Portfolio (BCG Matrix): Cắt Gì, Đẩy Gì?

**📌 Câu hỏi kinh doanh:**
> "Trong 1000+ SKU, cái nào đang gánh team, cái nào đang kéo lùi profit?"

**🎯 Mục tiêu:**
BCG Matrix phân loại toàn bộ product portfolio:
- **Stars** — Revenue cao + Margin cao + Return thấp → Đẩy mạnh
- **Cash Cows** — Revenue cao + Margin thấp → Giữ, tối ưu cost
- **Question Marks** — Revenue thấp + Margin cao → Test & scale
- **Dogs** — Revenue thấp + Margin thấp + Return cao → Review/Dừng

**📊 Data sử dụng:**
- `products` — price, cogs, category, segment, size
- `order_items` — quantity, revenue per product
- `returns` — return_rate per product
- `inventory` — days_of_supply, stockout_flag, overstock_flag

**📈 Output kỳ vọng (Bubble chart — axes: Revenue % × Margin %, size = return_rate):**

```
Stars (prioritize):   Áo Polo Premium, Streetwear M/L   → 35% revenue, 42% margin
Cash Cows (maintain): Basic Tee, Jeans Standard          → 28% revenue, 18% margin
Question Marks:       Activewear Female Series           → Test với email campaign
Dogs (review):        47 SKU summer jackets              → 2% revenue, margin âm
```

**💡 Prescriptive Output:**
> "**Dừng 47 SKU Dogs** → giải phóng warehouse + vốn = A triệu.  
> **Tăng inventory Stars 150%** trước mùa cao điểm.  
> **Launch test:** Activewear Female với micro-campaign email → target 25-34 tuổi."

**⚙️ Độ phức tạp:** ⭐⭐⭐ Cao (BCG bubble chart + multi-metric) | **⏱️ Ước tính:** 4–5 giờ  
**🎯 Điểm thi:** Rất cao — sáng tạo, đa chiều, actionable rõ ràng

---

## 🪟 WINDOW 8 — Geographic Revenue Map: Mở Rộng Thị Trường Ở Đâu?

**📌 Câu hỏi kinh doanh:**
> "Vùng nào đang ngủ quên — có khách nhưng revenue thấp vì lý do có thể fix?"

**🎯 Mục tiêu:**
Phân tích **revenue per customer** theo region để phân biệt "thị trường nhỏ thật sự" vs
"thị trường lớn nhưng đang bị underserved do logistics/marketing thấp".

**📊 Data sử dụng:**
- `geography` — region, district, zip
- `customers` + `orders` → Revenue by region
- `shipments` — delivery performance by region (liên kết Window 6)

**📈 Output kỳ vọng:**

```
Region   | # Customers | Revenue share | Rev/Customer | SLA    | Verdict
East     | 285,000     | 45%           | HIGH         | 89%    | ✅ Tốt
West     | 198,000     | 35%           | MEDIUM       | 87%    | ⚠️ Có thể tăng
Central  | 163,000     | 20%           | LOW          | 66%    | 🚨 Underserved
```

**💡 Prescriptive Output:**
> "Central: 163k khách nhưng SLA 66% — revenue thấp vì logistics tệ, không phải do demand thấp.  
> **Fix logistics trước khi marketing ở Central** → nếu SLA lên 85%, revenue tăng ước tính +30%.  
> **Expansion candidate:** District X, Y của West — YoY growth 40%, chưa bão hòa."

**⚙️ Độ phức tạp:** ⭐⭐ Thấp-Trung bình | **⏱️ Ước tính:** 2–3 giờ  
**🎯 Điểm thi:** Trung bình — good untuk data storytelling, liên kết Window 6

---

## 📋 Bảng Xác Nhận — Điền Quyết Định Vào Đây

| # | Window | Trọng tâm | Impact | Thời gian | Quyết định của bạn |
|---|--------|-----------|--------|-----------|-------------------|
| 1 | Promotion ROI | Margin & Promo effectiveness | ⭐⭐⭐⭐ | 3–4h | `✅ / ❌ / ⚠️` |
| 2 | Return Rate Deep-Dive | Causal chain of returns | ⭐⭐⭐⭐ | 3–4h | `✅ / ❌ / ⚠️` |
| 3 | Customer RFM | CLV & Retention priority | ⭐⭐⭐⭐⭐ | 4–5h | `✅ / ❌ / ⚠️` |
| 4 | Seasonal Planning | Inventory + Demand forecast | ⭐⭐⭐⭐ | 4–5h | `✅ / ❌ / ⚠️` |
| 5 | Marketing Channel ROI | Traffic quality vs volume | ⭐⭐⭐ | 2–3h | `✅ / ❌ / ⚠️` |
| 6 | Logistics & SLA | Delivery → Rating → Revenue | ⭐⭐⭐⭐ | 3–4h | `✅ / ❌ / ⚠️` |
| 7 | Product Portfolio (BCG) | Portfolio optimization | ⭐⭐⭐⭐⭐ | 4–5h | `✅ / ❌ / ⚠️` |
| 8 | Geographic Map | Market expansion | ⭐⭐⭐ | 2–3h | `✅ / ❌ / ⚠️` |

**Tổng nếu làm cả 8:** ~25–33 giờ coding + narrative

---

## 🎯 Gợi Ý Chiến Lược (Nếu Thời Gian Hạn Chế)

> [!IMPORTANT]
> **Gói 4 window tối thiểu — điểm cao nhất theo rubric:**
> **Window 3 (RFM) + Window 7 (BCG) + Window 2 (Return) + Window 4 (Seasonal)**
>
> Lý do: 4 phân tích này có **cross-table depth** + **actionable numbers** cao nhất.
> Đúng với tiêu chí *"Prescriptive nhất quán trên nhiều phân tích"* của ban giám khảo.

> [!TIP]
> Window 5 và 8 có thể làm gọn trong ~1.5h mỗi cái nếu ghép chung với Window 3 và 6.
> Window 6 (Logistics) cho điểm creativity cao vì kết nối 5 bảng dữ liệu.

---

> Sau khi bạn xác nhận, tôi sẽ implement từng window theo thứ tự với:
> - Code sạch, comments giải thích bằng tiếng Việt cho business team
> - Output = table + chart + markdown narrative (không phải chỉ raw code)
> - Mỗi section kết thúc bằng box **"💡 Khuyến nghị cho Ban Lãnh Đạo"** rõ ràng
