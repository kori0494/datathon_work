"""
data_pipeline.py — E-commerce Datathon ETL Pipeline
=====================================================
Project : Optimizing the Ecommerce Ecosystem (Fashion)
Data    : 2012 – 2024  |  15 CSV files
Output  : master_dataset.csv  (daily analytical file, Prophet/XGBoost-ready)

Table 1 — File inventory (official schema)
──────────────────────────────────────────
Layer        #  File
Master       1  products.csv              Danh mục sản phẩm
Master       2  customers.csv             Thông tin khách hàng
Master       3  promotions.csv            Các chiến dịch khuyến mãi
Master       4  geography.csv             Danh sách mã bưu chính các vùng
Transaction  5  orders.csv                Thông tin đơn hàng
Transaction  6  order_items.csv           Chi tiết từng dòng sản phẩm trong đơn
Transaction  7  payments.csv              Thông tin thanh toán (1:1 với đơn hàng)
Transaction  8  shipments.csv             Thông tin vận chuyển
Transaction  9  returns.csv               Các sản phẩm bị trả lại
Transaction 10  reviews.csv               Đánh giá sản phẩm sau giao hàng
Analytical  11  sales.csv                 Dữ liệu doanh thu huấn luyện
Analytical  12  sample_submission.csv     Định dạng file nộp bài (mẫu)
Operational 13  inventory.csv             Ảnh chụp tồn kho cuối tháng
Operational 14  inventory_enhanced.csv    Tồn kho mở rộng với các chỉ số dẫn xuất
Operational 15  web_traffic.csv           Lưu lượng truy cập website hàng ngày

Pipeline stages
───────────────
  load_data()                →  raw dict of DataFrames
  clean_data(dfs)            →  cleaned dict of DataFrames
  merge_tables(dfs)          →  master fact-level DataFrame (item-level)
  create_analytical_file()   →  daily aggregated DataFrame (≈ sales.csv structure)

Baseline reference: baseline.ipynb (seasonal-average + trend model)
"""

import warnings
import logging
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import holidays as _holidays_lib   # pip install holidays
    _HAS_HOLIDAYS = True
except ImportError:
    _HAS_HOLIDAYS = False

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data/")
OUT_FILE = DATA_DIR / "master_dataset.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Canonical 15-file manifest (Table 1) ─────────────────────────────────────
_ALL_FILES = list(dict.fromkeys([
    # Master layer (dimensions)
    "products.csv",               # 1
    "customers.csv",              # 2
    "promotions.csv",             # 3
    "geography.csv",              # 4
    # Transaction layer
    "orders.csv",                 # 5
    "order_items.csv",            # 6
    "payments.csv",               # 7
    "shipments.csv",              # 8
    "returns.csv",                # 9
    "reviews.csv",                # 10  — Transaction (post-delivery ratings)
    # Analytical layer
    "sales.csv",                  # 11
    "sample_submission.csv",      # 12
    # Operational layer
    "inventory.csv",              # 13
    "inventory_enhanced.csv",     # 14  — Extended inventory with derived KPIs
    "web_traffic.csv",            # 15
]))


# ─────────────────────────────────────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _cast_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Cast every column whose name contains 'date' to datetime (baseline §2)."""
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _log_shape(label: str, before: tuple, after: tuple) -> None:
    """Log shape change after a join — mirrors baseline §6 sanity-check pattern."""
    delta = after[0] - before[0]
    sign  = "+" if delta >= 0 else ""
    log.info("  %-45s  %s → %s  (rows %s%d)", label, before, after, sign, delta)


def _check_fanout(df: pd.DataFrame, key, step: str) -> None:
    """Warn when a join inflates rows unexpectedly (accidental cross-join / fan-out)."""
    n_dup = df.duplicated(subset=key).sum()
    if n_dup:
        log.warning("  ⚠  Fan-out at [%s] — %d duplicate rows on key %s",
                    step, n_dup, key)
    else:
        log.info("  ✓  No fan-out at [%s]", step)


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_data(data_dir: str | Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """
    Read all 15 CSV files from *data_dir* (Table 1 official schema).
    • Auto-casts every *date* column to datetime (baseline §2 pattern).
    • Files not found are skipped with a WARNING — pipeline continues gracefully.

    Layer mapping (Table 1)
    ───────────────────────
    Master      : products, customers, promotions, geography
    Transaction : orders, order_items, payments, shipments, returns, reviews
    Analytical  : sales, sample_submission
    Operational : inventory, inventory_enhanced, web_traffic

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are file stems, e.g. 'orders', 'inventory_enhanced', 'sales', …
    """
    data_dir = Path(data_dir)
    log.info("═" * 65)
    log.info("STAGE 1 — LOAD DATA  (source: %s)", data_dir.resolve())
    log.info("═" * 65)

    # Layer labels for human-readable logs
    _LAYER = {
        "products": "Master", "customers": "Master",
        "promotions": "Master", "geography": "Master",
        "orders": "Transaction", "order_items": "Transaction",
        "payments": "Transaction", "shipments": "Transaction",
        "returns": "Transaction", "reviews": "Transaction",
        "sales": "Analytical", "sample_submission": "Analytical",
        "inventory": "Operational", "inventory_enhanced": "Operational",
        "web_traffic": "Operational",
    }

    dfs: dict[str, pd.DataFrame] = {}

    for fname in _ALL_FILES:
        path  = data_dir / fname
        key   = fname.replace(".csv", "")
        layer = _LAYER.get(key, "Unknown")

        if not path.exists():
            log.warning("  SKIP  [%-11s]  %-28s  (file not found)", layer, fname)
            continue

        df = pd.read_csv(path)
        df = _cast_dates(df)
        log.info("  LOAD  [%-11s]  %-28s  shape=%s", layer, fname, df.shape)
        dfs[key] = df

    # ── Sanity: warn if inventory_enhanced is absent (new in this schema version)
    if "inventory_enhanced" not in dfs:
        log.warning("inventory_enhanced.csv not found — "
                    "extended inventory KPIs will be unavailable downstream.")

    # ── Sanity: reviews is a required Transaction table
    if "reviews" not in dfs:
        log.warning("reviews.csv not found — "
                    "post-delivery ratings unavailable downstream.")

    log.info("Loaded %d / %d files.", len(dfs), len(_ALL_FILES))
    return dfs


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — CLEAN DATA
# ─────────────────────────────────────────────────────────────────────────────

def clean_data(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Apply business-rule validation and missing-value treatment.

    Rules applied
    ─────────────
    customers   : fill 'Unknown' for gender, age_group (categorical nulls)
    products    : drop rows where cogs >= price  (margin constraint violation)
    promotions  : fill 'All' for null applicable_category
    orders      : retain only recognised order statuses
    order_items : drop non-positive quantity / unit_price rows

    Returns the same dict with cleaned DataFrames.
    """
    log.info("═" * 65)
    log.info("STAGE 2 — CLEAN DATA")
    log.info("═" * 65)

    # ── customers ─────────────────────────────────────────────────────────────
    if "customers" in dfs:
        cust = dfs["customers"]
        for col in ["gender", "age_group"]:
            if col in cust.columns:
                n = cust[col].isna().sum()
                cust[col] = cust[col].fillna("Unknown")
                log.info("  customers.%-12s  filled %d nulls → 'Unknown'", col, n)
        dfs["customers"] = cust

    # ── products ──────────────────────────────────────────────────────────────
    if "products" in dfs:
        prod   = dfs["products"]
        before = len(prod)
        prod   = prod[prod["cogs"] < prod["price"]].copy()
        log.info("  products: dropped %d rows with cogs >= price  (kept %d)",
                 before - len(prod), len(prod))
        dfs["products"] = prod

    # ── promotions ────────────────────────────────────────────────────────────
    if "promotions" in dfs:
        promo = dfs["promotions"]
        if "applicable_category" in promo.columns:
            n = promo["applicable_category"].isna().sum()
            promo["applicable_category"] = promo["applicable_category"].fillna("All")
            log.info("  promotions.applicable_category  filled %d nulls → 'All'", n)
        dfs["promotions"] = promo

    # ── orders ────────────────────────────────────────────────────────────────
    if "orders" in dfs:
        ord_   = dfs["orders"]
        valid  = {"shipped", "delivered", "returned", "processing",
                  "cancelled", "pending"}
        before = len(ord_)
        ord_   = ord_[ord_["order_status"].str.lower().isin(valid)].copy()
        log.info("  orders: dropped %d rows with unrecognised status  (kept %d)",
                 before - len(ord_), len(ord_))
        dfs["orders"] = ord_

    # ── order_items ───────────────────────────────────────────────────────────
    if "order_items" in dfs:
        oi     = dfs["order_items"]
        before = len(oi)
        oi     = oi[(oi["quantity"] > 0) & (oi["unit_price"] > 0)].copy()
        log.info("  order_items: dropped %d non-positive rows  (kept %d)",
                 before - len(oi), len(oi))
        dfs["order_items"] = oi

    # ── reviews  (Transaction #10) ────────────────────────────────────────────
    # Drop reviews with no order_id linkage; fill missing rating with median.
    if "reviews" in dfs:
        rev    = dfs["reviews"]
        before = len(rev)
        rev    = rev.dropna(subset=["order_id"]).copy()
        log.info("  reviews: dropped %d rows with null order_id  (kept %d)",
                 before - len(rev), len(rev))
        if "rating" in rev.columns:
            n = rev["rating"].isna().sum()
            rev["rating"] = rev["rating"].fillna(rev["rating"].median())
            log.info("  reviews.rating  filled %d nulls → median (%.1f)",
                     n, rev["rating"].median())
        dfs["reviews"] = rev

    # ── inventory_enhanced  (Operational #14) ────────────────────────────────
    # Drop rows with null product_id or snapshot_date (meaningless without a key).
    if "inventory_enhanced" in dfs:
        inv_e  = dfs["inventory_enhanced"]
        before = len(inv_e)
        key_cols = [c for c in ["product_id", "snapshot_date"] if c in inv_e.columns]
        inv_e    = inv_e.dropna(subset=key_cols).copy()
        log.info("  inventory_enhanced: dropped %d rows with null key cols %s  (kept %d)",
                 before - len(inv_e), key_cols, len(inv_e))
        # Clip any derived KPI ratios to [0, 1] range if present
        for ratio_col in ["sell_through_rate", "fill_rate", "stockout_rate"]:
            if ratio_col in inv_e.columns:
                inv_e[ratio_col] = inv_e[ratio_col].clip(0.0, 1.0)
                log.info("  inventory_enhanced.%-20s  clipped to [0, 1]", ratio_col)
        dfs["inventory_enhanced"] = inv_e

    log.info("Clean stage complete.")
    return dfs


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — MERGE TABLES
# ─────────────────────────────────────────────────────────────────────────────

def merge_tables(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build the master item-level fact table via progressive joins (Star Schema).

    ┌─────────────────────────────────────────────────────────────────┐
    │  Join strategy & rationale                                      │
    ├─────────────────────────────────────────────────────────────────┤
    │  Step 1 — Transaction core                                      │
    │    order_items LEFT JOIN orders                                 │
    │      • LEFT: keeps every item line; an order header may be      │
    │        missing due to upstream cleaning but we must NOT silently │
    │        lose revenue rows.                                       │
    │      • orders is the spine — all dimension FK keys live here.   │
    │    + LEFT JOIN payments   (1:1 — pending orders may lack rows)  │
    │    + LEFT JOIN shipments  (1:0/1 — only fulfilled orders exist) │
    │                                                                 │
    │  Step 2 — Dimension enrichment                                  │
    │    + LEFT JOIN products   (cogs, category — needed for profit)  │
    │    + LEFT JOIN customers  → geography                           │
    │      • LEFT throughout: missing dimension keys are a data-      │
    │        quality issue, not a reason to drop real transactions.   │
    │                                                                 │
    │  Step 3 — Returns                                               │
    │    Aggregate returns to (order_id, product_id) BEFORE joining   │
    │    to prevent fan-out (one item returned N times → N rows).     │
    │    + LEFT JOIN returns_agg                                      │
    │                                                                 │
    │  Step 4 — Financial calculations                                │
    │    Net_Revenue  = (qty × unit_price) − discount_amount          │
    │    Actual_Profit = Net_Revenue − (qty × cogs) − refund_amount   │
    └─────────────────────────────────────────────────────────────────┘

    Returns
    -------
    pd.DataFrame  — one row per order × product item line
    """
    log.info("═" * 65)
    log.info("STAGE 3 — MERGE TABLES")
    log.info("═" * 65)

    # ── Unpack tables ─────────────────────────────────────────────────────────
    oi   = dfs["order_items"].copy()
    ord_ = dfs["orders"].copy()
    pay  = dfs.get("payments",  pd.DataFrame()).copy()
    ship = dfs.get("shipments", pd.DataFrame()).copy()
    prod = dfs.get("products",  pd.DataFrame()).copy()
    cust = dfs.get("customers", pd.DataFrame()).copy()
    geo  = dfs.get("geography", pd.DataFrame()).copy()
    ret  = dfs.get("returns",   pd.DataFrame()).copy()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1 — TRANSACTION CORE
    # ─────────────────────────────────────────────────────────────────────────

    # 1-a  order_items LEFT JOIN orders (spine / backbone)
    before = oi.shape
    fact   = oi.merge(ord_, on="order_id", how="left", suffixes=("", "_ord"))
    _log_shape("order_items LEFT JOIN orders (spine)", before, fact.shape)
    _check_fanout(fact, ["order_id", "product_id"], "items × orders")

    # 1-b  LEFT JOIN payments  (1:1 — drop duplicate payment_method column)
    if not pay.empty:
        pay_slim = pay.drop(columns=["payment_method"], errors="ignore")
        before   = fact.shape
        fact     = fact.merge(pay_slim, on="order_id", how="left")
        _log_shape("LEFT JOIN payments (1:1)", before, fact.shape)

    # 1-c  LEFT JOIN shipments  (1:0/1 — only shipped/delivered/returned)
    if not ship.empty:
        before = fact.shape
        fact   = fact.merge(ship, on="order_id", how="left")
        _log_shape("LEFT JOIN shipments (1:0/1)", before, fact.shape)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2 — DIMENSION ENRICHMENT
    # ─────────────────────────────────────────────────────────────────────────

    # 2-a  LEFT JOIN products
    if not prod.empty:
        prod_cols = ["product_id"] + [
            c for c in ["product_name", "category", "segment", "price", "cogs"]
            if c in prod.columns
        ]
        before = fact.shape
        fact   = fact.merge(prod[prod_cols], on="product_id", how="left",
                            suffixes=("_item", "_prod"))
        _log_shape("LEFT JOIN products", before, fact.shape)

    # Resolve cogs column (may have suffix after merge with order_items)
    cogs_col = "cogs_prod" if "cogs_prod" in fact.columns else "cogs"

    # 2-b  LEFT JOIN customers + geography (zip → region, district)
    if not cust.empty:
        cust_geo = cust.copy()
        if not geo.empty:
            geo_slim = geo.drop(columns=["city"], errors="ignore")   # avoid city collision
            cust_geo = cust_geo.merge(geo_slim, on="zip", how="left")
            log.info("  customers enriched with geography: %s", cust_geo.shape)

        cust_geo = cust_geo.drop(columns=["zip"], errors="ignore")   # zip already on orders
        before   = fact.shape
        fact     = fact.merge(cust_geo, on="customer_id", how="left",
                              suffixes=("", "_cust"))
        _log_shape("LEFT JOIN customers + geography", before, fact.shape)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3 — RETURNS  (pre-aggregate to avoid fan-out)
    # ─────────────────────────────────────────────────────────────────────────
    if not ret.empty:
        ret_agg = (
            ret
            .groupby(["order_id", "product_id"], as_index=False)
            .agg(
                return_quantity = ("return_quantity", "sum"),
                refund_amount   = ("refund_amount",   "sum"),
                return_date     = ("return_date",     "min"),   # earliest return
            )
        )
        before = fact.shape
        fact   = fact.merge(ret_agg, on=["order_id", "product_id"], how="left")
        _log_shape("LEFT JOIN returns (pre-aggregated)", before, fact.shape)
        _check_fanout(fact, ["order_id", "product_id"], "items × returns")

    # Fill 0 for items with no return record
    fact["return_quantity"] = fact["return_quantity"].fillna(0).astype(int)
    fact["refund_amount"]   = fact["refund_amount"].fillna(0.0)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3-b — REVIEWS  (Transaction #10 — post-delivery ratings)
    # ─────────────────────────────────────────────────────────────────────────
    # Reviews join on order_id only (not product_id — one review per order).
    # We aggregate to order level first to keep cardinality 1:1 with orders,
    # then left-join so that items belonging to unreviewed orders keep their rows.
    rev = dfs.get("reviews", pd.DataFrame()).copy()
    if not rev.empty and "order_id" in rev.columns:
        rev_cols = ["order_id"] + [
            c for c in ["rating", "review_score", "review_date", "sentiment"]
            if c in rev.columns
        ]
        rev_agg = (
            rev[rev_cols]
            .groupby("order_id", as_index=False)
            .agg({c: "mean" if rev[c].dtype in [float, int] else "first"
                  for c in rev_cols if c != "order_id"})
        )
        before = fact.shape
        fact   = fact.merge(rev_agg, on="order_id", how="left")
        _log_shape("LEFT JOIN reviews (order-level agg)", before, fact.shape)
        log.info("  reviews coverage: %.1f%% of fact rows have a rating",
                 fact["rating"].notna().mean() * 100 if "rating" in fact.columns else 0)
    else:
        log.info("  reviews: not available — skipped")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4 — FINANCIAL CALCULATIONS
    # ─────────────────────────────────────────────────────────────────────────

    #   Net_Revenue  = (quantity × unit_price) − discount_amount
    #   NOTE: refund_amount is stored on the fact row for reference but is NOT
    #         subtracted here. Refunds are deducted on the actual return_date
    #         inside create_analytical_file() — not on the original order_date.
    #         Subtracting here would silently distort historical daily Revenue.
    fact["discount_amount"] = fact["discount_amount"].fillna(0.0) \
        if "discount_amount" in fact.columns else 0.0
    fact["Net_Revenue"] = (
        fact["quantity"] * fact["unit_price"] - fact["discount_amount"]
    ).round(4)

    #   Actual_Profit (before returns) = Net_Revenue − (quantity × cogs)
    #   Returns are handled in create_analytical_file() on return_date.
    if cogs_col in fact.columns:
        fact["COGS_Line"]     = (fact["quantity"] * fact[cogs_col]).round(4)
        fact["Actual_Profit"] = (fact["Net_Revenue"] - fact["COGS_Line"]).round(4)
    else:
        log.warning("  cogs column not found — COGS_Line & Actual_Profit will be NaN")
        fact["COGS_Line"]     = np.nan
        fact["Actual_Profit"] = np.nan

    fact["is_returned"] = (fact["return_quantity"] > 0).astype(int)

    log.info("Financial columns: Net_Revenue, COGS_Line, Actual_Profit, is_returned")
    log.info("Master fact table: %d rows × %d cols", *fact.shape)

    return fact


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — CREATE ANALYTICAL FILE  (daily aggregate ≈ sales.csv)
# ─────────────────────────────────────────────────────────────────────────────

def create_analytical_file(
    merged_df: pd.DataFrame,
    promotions: pd.DataFrame | None = None,
    web_traffic: pd.DataFrame | None = None,
    sales_ref: pd.DataFrame | None = None,
    inventory_enhanced: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Aggregate the item-level fact table to a *daily* time-series file that:
    • mirrors the structure of sales.csv  →  Date, Revenue, COGS
    • adds feature columns ready for Prophet / XGBoost

    Extra features (baseline §3 feature-engineering pattern)
    ─────────────────────────────────────────────────────────
    Calendar     : year, month, day, day_of_year, day_of_week, quarter, is_weekend
    Holiday      : is_holiday (rolling-window spike + VN public holidays)
    Promo        : is_promo   (1 if any promotion active that day)
    Traffic      : sessions, unique_visitors, bounce_rate, conversion_rate
    Inventory    : monthly inventory KPIs from inventory_enhanced (#14) merged on
                   year-month — stock_on_hand, sell_through_rate, stockout_days, etc.
    Trend ref    : yoy_growth_ref — geometric mean YoY growth (baseline §3 method)
    Sales ref    : Revenue_ref, COGS_ref, revenue_mape_day — vs historical sales.csv
    """
    log.info("═" * 65)
    log.info("STAGE 4 — CREATE ANALYTICAL FILE")
    log.info("═" * 65)

    df = merged_df.copy()

    # ── 4-a: Identify the order date column ──────────────────────────────────
    date_col = "order_date" if "order_date" in df.columns else "Date"
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["_date"] = df[date_col].dt.normalize()

    # ── 4-b: Daily aggregation (Revenue & Profit BEFORE returns) ─────────────
    # We deliberately exclude refund_amount here.
    # Returns impact will be joined in on return_date (see 4-b2 below).
    daily = (
        df
        .groupby("_date")
        .agg(
            Revenue          = ("Net_Revenue",    "sum"),
            COGS             = ("COGS_Line",       "sum"),
            Actual_Profit    = ("Actual_Profit",   "sum"),
            n_orders         = ("order_id",        "nunique"),
            n_items          = ("quantity",        "sum"),
        )
        .reset_index()
        .rename(columns={"_date": "Date"})
        .sort_values("Date")
        .reset_index(drop=True)
    )

    # ── 4-b2: Subtract refunds on ACTUAL return_date  ─────────────────────────
    # ⚠️  Critical correctness fix: refund_amount must hit the day the customer
    #     actually returned the item (return_date), NOT the original order_date.
    #     Applying it on order_date would silently corrupt historical Revenue.
    #     We build a separate daily-returns series and subtract it in.
    if "return_date" in df.columns and "refund_amount" in df.columns:
        ret_daily = (
            df[df["return_date"].notna()]
            .assign(_ret_date=lambda x: x["return_date"].dt.normalize())
            .groupby("_ret_date", as_index=False)
            .agg(
                n_returned_items = ("return_quantity", "sum"),
                total_refunds    = ("refund_amount",   "sum"),
            )
            .rename(columns={"_ret_date": "Date"})
        )

        # Merge returns onto the calendar of order dates
        daily = daily.merge(ret_daily, on="Date", how="left")
        daily["n_returned_items"] = daily["n_returned_items"].fillna(0).astype(int)
        daily["total_refunds"]    = daily["total_refunds"].fillna(0.0)

        # Adjust Revenue and Profit for the day returns actually occurred
        daily["Revenue"]       = (daily["Revenue"]       - daily["total_refunds"]).round(4)
        daily["Actual_Profit"] = (daily["Actual_Profit"] - daily["total_refunds"]).round(4)

        n_neg = (daily["Revenue"] < 0).sum()
        if n_neg:
            log.warning("  ⚠  %d days have negative Revenue after return deduction "
                        "(high-refund days — expected for heavy-return periods)", n_neg)
        log.info("Returns deducted on return_date: %d return-days  |  "
                 "total_refunds=%.2f", len(ret_daily), daily["total_refunds"].sum())
    else:
        daily["n_returned_items"] = 0
        daily["total_refunds"]    = 0.0
        log.info("return_date or refund_amount not found — returns deduction skipped")

    log.info("Daily aggregation: %d rows  (%s → %s)",
             len(daily), daily["Date"].min().date(), daily["Date"].max().date())
    daily["year"]        = daily["Date"].dt.year
    daily["month"]       = daily["Date"].dt.month
    daily["day"]         = daily["Date"].dt.day
    daily["day_of_year"] = daily["Date"].dt.dayofyear   # baseline uses this directly
    daily["day_of_week"] = daily["Date"].dt.dayofweek   # 0=Mon, 6=Sun
    daily["quarter"]     = daily["Date"].dt.quarter
    daily["is_weekend"]  = (daily["day_of_week"] >= 5).astype(int)

    # ── 4-d: is_holiday ───────────────────────────────────────────────────────
    # Method A — revenue spike (same rolling window used in baseline §6 validation)
    daily = daily.sort_values("Date").reset_index(drop=True)
    roll_mean = daily["Revenue"].rolling(30, min_periods=7, center=True).mean()
    roll_std  = daily["Revenue"].rolling(30, min_periods=7, center=True).std()
    spike     = daily["Revenue"] > (roll_mean + 2 * roll_std)

    # Method B — Official Vietnamese public holidays via `holidays` library
    # This correctly resolves Tết Nguyên Đán to its exact Gregorian date each year
    # (e.g. Tết 2023 = Jan 22, Tết 2024 = Feb 10) rather than a fixed approximation.
    try:
        if not _HAS_HOLIDAYS:
            raise ImportError
        years_in_data = daily["Date"].dt.year.unique().tolist()
        vn_holidays   = _holidays_lib.Vietnam(years=years_in_data)

        # Extend window: flag the 2 days BEFORE and 3 days AFTER each official holiday
        # — fashion sales spike strongly in the run-up to Tết.
        holiday_dates: set[pd.Timestamp] = set()
        for hdate in vn_holidays.keys():
            for offset in range(-2, 4):   # -2 … +3 days inclusive
                holiday_dates.add(pd.Timestamp(hdate) + pd.Timedelta(days=offset))

        cal_holiday = daily["Date"].isin(holiday_dates)
        log.info("is_holiday [holidays lib]: %d official VN holidays across %d years  "
                 "(with ±window: %d days flagged)",
                 len(vn_holidays), len(years_in_data), cal_holiday.sum())
    except ImportError:
        log.warning("  'holidays' library not installed — "
                    "falling back to static VN holiday list. "
                    "Install with: pip install holidays")
        VN_FALLBACK = {(1,1),(4,29),(4,30),(5,1),(9,2)}
        cal_holiday  = daily["Date"].apply(lambda d: (d.month, d.day) in VN_FALLBACK)

    daily["is_holiday"] = (spike | cal_holiday).astype(int)
    log.info("is_holiday final: %d days flagged  (spike=%d  calendar=%d)",
             daily["is_holiday"].sum(), spike.sum(), cal_holiday.sum())

    # ── 4-e: is_promo ─────────────────────────────────────────────────────────
    if promotions is not None and not promotions.empty:
        promo = promotions.copy()
        promo["start_date"] = pd.to_datetime(promo["start_date"], errors="coerce")
        promo["end_date"]   = pd.to_datetime(promo["end_date"],   errors="coerce")
        promo = promo.dropna(subset=["start_date", "end_date"])

        def _is_promo(date: pd.Timestamp) -> int:
            return int(
                ((promo["start_date"] <= date) & (promo["end_date"] >= date)).any()
            )

        daily["is_promo"] = daily["Date"].apply(_is_promo)
        log.info("is_promo: %d days have an active promotion", daily["is_promo"].sum())
    else:
        daily["is_promo"] = 0
        log.info("is_promo: promotions table not supplied — defaulted to 0")

    # ── 4-f: Web traffic ──────────────────────────────────────────────────────
    if web_traffic is not None and not web_traffic.empty:
        wt = web_traffic.copy()
        wt_date_col = "date" if "date" in wt.columns else "Date"
        wt[wt_date_col] = pd.to_datetime(wt[wt_date_col], errors="coerce")
        wt = wt.rename(columns={wt_date_col: "Date"})
        before = len(daily)
        daily  = daily.merge(wt, on="Date", how="left")
        matched = daily["sessions"].notna().sum() if "sessions" in daily.columns else 0
        log.info("web_traffic merged: %d / %d rows matched", matched, before)
    else:
        log.info("web_traffic: not supplied — skipped")

    # ── 4-g: inventory_enhanced  (Operational #14) ────────────────────────────
    # inventory_enhanced is a monthly snapshot (1 row/product/month).
    # Strategy:
    #   1. Aggregate all products → 1 row per (year, month) with portfolio-level KPIs.
    #   2. Left-join onto daily by (year, month) — each day inherits that month's KPIs.
    #   3. Assert row count is UNCHANGED after join (monthly join should never fan-out).
    if inventory_enhanced is not None and not inventory_enhanced.empty:
        inv_e = inventory_enhanced.copy()

        snap_col = next(
            (c for c in inv_e.columns if "snapshot" in c.lower() or "date" in c.lower()),
            None
        )
        if snap_col:
            inv_e[snap_col] = pd.to_datetime(inv_e[snap_col], errors="coerce")
            inv_e["_year"]  = inv_e[snap_col].dt.year
            inv_e["_month"] = inv_e[snap_col].dt.month

            numeric_cols = inv_e.select_dtypes(include="number").columns.tolist()
            agg_dict = {c: "mean" for c in numeric_cols if c not in ["_year", "_month"]}
            for qty_col in ["stock_on_hand", "units_sold", "stockout_days"]:
                if qty_col in agg_dict:
                    agg_dict[qty_col] = "sum"

            inv_monthly = (
                inv_e.groupby(["_year", "_month"], as_index=False)
                     .agg(agg_dict)
                     .rename(columns=lambda c: f"inv_{c}"
                             if c not in ("_year", "_month") else c)
            )

            # ── GUARD: confirm 1 row per (year, month) before joining ─────────
            n_before_join = len(daily)
            assert inv_monthly.duplicated(["_year","_month"]).sum() == 0, \
                "inventory_enhanced monthly agg has duplicates — join will fan-out!"

            daily = daily.merge(inv_monthly,
                                left_on=["year", "month"],
                                right_on=["_year", "_month"],
                                how="left")
            daily.drop(columns=["_year", "_month"], errors="ignore", inplace=True)

            # ── CRITICAL CHECK: row count must be identical after join ─────────
            if len(daily) != n_before_join:
                raise RuntimeError(
                    f"Inventory join inflated rows: {n_before_join} → {len(daily)}. "
                    "Monthly aggregate likely has duplicate (year, month) keys."
                )

            inv_cols   = [c for c in daily.columns if c.startswith("inv_")]
            matched    = daily[inv_cols[0]].notna().sum() if inv_cols else 0
            log.info("inventory_enhanced merged  ✓  rows unchanged=%d  "
                     "matched=%d/%d  inv_cols=%d",
                     n_before_join, matched, n_before_join, len(inv_cols))
        else:
            log.warning("inventory_enhanced: no date/snapshot column found — skipped")
    else:
        log.info("inventory_enhanced: not supplied — skipped")

    # ── 4-g: YoY growth reference (baseline §3 geometric mean pattern) ────────
    # Mirrors: growth_rev = (1 + yoy_rev).prod() ** (1 / len(yoy_rev))
    if daily["year"].nunique() > 1:
        annual    = daily.groupby("year")["Revenue"].sum().reset_index().sort_values("year")
        yoy_rates = annual["Revenue"].pct_change().dropna()
        if len(yoy_rates) > 0:
            growth_rate = float((1 + yoy_rates).prod() ** (1 / len(yoy_rates)))
            log.info("Geometric mean YoY Revenue growth: %.4f  (%.2f%%/yr)",
                     growth_rate, (growth_rate - 1) * 100)
            daily["yoy_growth_ref"] = growth_rate
        else:
            daily["yoy_growth_ref"] = np.nan
    else:
        daily["yoy_growth_ref"] = np.nan

    # ── 4-h: Comparison vs historical sales.csv (baseline §6 MAPE check) ──────
    if sales_ref is not None and not sales_ref.empty:
        ref = sales_ref.copy()
        ref["Date"] = pd.to_datetime(ref["Date"], errors="coerce")
        ref = ref.rename(columns={"Revenue": "Revenue_ref", "COGS": "COGS_ref"})
        daily = daily.merge(ref[["Date", "Revenue_ref", "COGS_ref"]], on="Date", how="left")

        # Day-level MAPE — same metric used in baseline §6
        mask = daily["Revenue_ref"].notna() & (daily["Revenue_ref"] != 0)
        daily.loc[mask, "revenue_mape_day"] = (
            (daily.loc[mask, "Revenue"] - daily.loc[mask, "Revenue_ref"]).abs()
            / daily.loc[mask, "Revenue_ref"]
        )
        if mask.sum() > 0:
            mape_pct = daily.loc[mask, "revenue_mape_day"].mean() * 100
            log.info("MAPE vs sales.csv reference (overlapping dates): %.2f%%", mape_pct)

    log.info("Analytical file complete: %d rows × %d cols", *daily.shape)
    return daily


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("╔" + "═" * 63 + "╗")
    log.info("║   E-COMMERCE ETL PIPELINE — START" + " " * 28 + "║")
    log.info("╚" + "═" * 63 + "╝")

    # Stage 1 — Load all 15 CSVs
    dfs = load_data(DATA_DIR)

    # Stage 2 — Clean & validate
    dfs = clean_data(dfs)

    # Stage 3 — Build item-level fact table
    master_fact = merge_tables(dfs)

    # Stage 4 — Aggregate to daily; add features
    daily_df = create_analytical_file(
        merged_df           = master_fact,
        promotions          = dfs.get("promotions"),
        web_traffic         = dfs.get("web_traffic"),
        sales_ref           = dfs.get("sales"),             # historical baseline reference
        inventory_enhanced  = dfs.get("inventory_enhanced"), # Operational #14
    )

    # Save master_dataset.csv
    daily_df.to_csv(OUT_FILE, index=False)
    log.info("✔  Saved → %s  (%d rows × %d cols)", OUT_FILE.resolve(), *daily_df.shape)

    log.info("╔" + "═" * 63 + "╗")
    log.info("║   PIPELINE COMPLETE" + " " * 43 + "║")
    log.info("╚" + "═" * 63 + "╝")