"""
app.py
------
E-Commerce Sales & Customer Analytics Dashboard (Streamlit + Plotly).

Run locally:
    streamlit run app/app.py

Notes:
- All numbers are computed live from data/ecommerce_clean.csv (or, if it
  doesn't exist yet, the app cleans data/ecommerce.csv on first load).
- Filters in the sidebar drive every KPI and chart on every page.
"""

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from data_cleaning import clean_pipeline          # noqa: E402
from rfm_analysis import calculate_rfm, segment_summary, SEGMENT_DESCRIPTIONS  # noqa: E402
from analysis import generate_insights            # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

st.set_page_config(
    page_title="E-Commerce Sales & Customer Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------
st.markdown("""
<style>
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 18px 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi-value { font-size: 26px; font-weight: 700; color: #1f2937; }
    .kpi-label { font-size: 13px; color: #6b7280; margin-bottom: 4px; }
    .insight-box {
        background-color: #f8fafc;
        border-left: 4px solid #2563eb;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 4px;
        font-size: 14.5px;
    }
    .section-title { font-size: 20px; font-weight: 700; margin-top: 10px; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and preparing data...")
def load_data():
    clean_path = os.path.join(DATA_DIR, "ecommerce_clean.csv")
    raw_path = os.path.join(DATA_DIR, "ecommerce.csv")

    if os.path.exists(clean_path):
        df = pd.read_csv(clean_path, parse_dates=["Order_Date"])
    else:
        df = clean_pipeline(raw_path=raw_path)

    rfm = calculate_rfm(df)
    return df, rfm


df, rfm = load_data()
df["Order_Date"] = pd.to_datetime(df["Order_Date"])

# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------
st.sidebar.title("📊 Filters")

min_date, max_date = df["Order_Date"].min().date(), df["Order_Date"].max().date()
date_range = st.sidebar.date_input(
    "Order Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

categories = st.sidebar.multiselect(
    "Category", options=sorted(df["Category"].unique()), default=[]
)
regions = st.sidebar.multiselect(
    "Region", options=sorted(df["Region"].unique()), default=[]
)
payment_modes = st.sidebar.multiselect(
    "Payment Mode", options=sorted(df["Payment_Mode"].unique()), default=[]
)
customer_search = st.sidebar.text_input("Search Customer (name or ID)", "")

filtered = df[
    (df["Order_Date"].dt.date >= start_date) & (df["Order_Date"].dt.date <= end_date)
]
if categories:
    filtered = filtered[filtered["Category"].isin(categories)]
if regions:
    filtered = filtered[filtered["Region"].isin(regions)]
if payment_modes:
    filtered = filtered[filtered["Payment_Mode"].isin(payment_modes)]
if customer_search:
    mask = (
        filtered["Customer_Name"].str.contains(customer_search, case=False, na=False)
        | filtered["Customer_ID"].str.contains(customer_search, case=False, na=False)
    )
    filtered = filtered[mask]

st.sidebar.markdown("---")
st.sidebar.caption(f"Data last updated: {df['Order_Date'].max().strftime('%d %b %Y')}")
st.sidebar.caption(f"Rows in view: {len(filtered):,} of {len(df):,}")

if filtered.empty:
    st.warning("No data matches the current filters. Adjust filters in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("🛒 E-Commerce Sales & Customer Analytics Dashboard")
st.caption(
    "An end-to-end business analytics project: data cleaning → EDA → SQL → "
    "customer segmentation → interactive dashboard. All figures below are "
    "computed live from the filtered dataset."
)

page = st.tabs(["📈 Executive Overview", "📦 Product Analysis",
                 "👥 Customer Analysis", "🗺️ Regional Analysis",
                 "🧠 Insights & About"])

# ---------------------------------------------------------------------
# KPI helper
# ---------------------------------------------------------------------
def kpi_card(col, label, value):
    col.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def compute_kpis(d: pd.DataFrame) -> dict:
    revenue = d["Sales"].sum()
    profit = d["Profit"].sum()
    orders = d["Order_ID"].nunique()
    aov = revenue / orders if orders else 0
    margin = (profit / revenue * 100) if revenue else 0
    return dict(revenue=revenue, profit=profit, orders=orders, aov=aov, margin=margin)


# =======================================================================
# TAB 1: EXECUTIVE OVERVIEW
# =======================================================================
with page[0]:
    k = compute_kpis(filtered)
    c1, c2, c3, c4, c5 = st.columns(5)
    kpi_card(c1, "Total Revenue", f"₹{k['revenue']:,.0f}")
    kpi_card(c2, "Total Profit", f"₹{k['profit']:,.0f}")
    kpi_card(c3, "Total Orders", f"{k['orders']:,}")
    kpi_card(c4, "Avg Order Value", f"₹{k['aov']:,.0f}")
    kpi_card(c5, "Profit Margin", f"{k['margin']:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    trend = (filtered.groupby(filtered["Order_Date"].dt.to_period("M").astype(str))
                      .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"))
                      .reset_index().rename(columns={"Order_Date": "Month"}))
    trend.columns = ["Month", "Revenue", "Profit"]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(trend, x="Month", y="Revenue", markers=True,
                       title="Monthly Revenue Trend")
        fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.line(trend, x="Month", y="Profit", markers=True,
                       title="Monthly Profit Trend", color_discrete_sequence=["#059669"])
        fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        cat_rev = filtered.groupby("Category", observed=True)["Sales"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(cat_rev, x="Sales", y="Category", orientation="h", title="Sales by Category")
        fig.update_layout(margin=dict(t=50, l=10, r=10, b=10), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        cat_profit = filtered.groupby("Category", observed=True)["Profit"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(cat_profit, x="Profit", y="Category", orientation="h", title="Profit by Category",
                     color_discrete_sequence=["#059669"])
        fig.update_layout(margin=dict(t=50, l=10, r=10, b=10), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    reg_rev = filtered.groupby("Region", observed=True)["Sales"].sum().sort_values(ascending=False).reset_index()
    fig = px.bar(reg_rev, x="Region", y="Sales", title="Sales by Region", color="Region")
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


# =======================================================================
# TAB 2: PRODUCT ANALYSIS
# =======================================================================
with page[1]:
    st.markdown('<div class="section-title">Top 10 Products by Revenue</div>', unsafe_allow_html=True)
    prod = (filtered.groupby(["Category", "Sub_Category"], observed=True)
                     .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
                          Orders=("Order_ID", "nunique"))
                     .assign(Profit_Margin_Pct=lambda x: (x["Profit"] / x["Revenue"] * 100).round(2))
                     .reset_index())

    top_rev = prod.sort_values("Revenue", ascending=False).head(10)
    fig = px.bar(top_rev, x="Revenue", y="Sub_Category", color="Category", orientation="h",
                 title="Top 10 Sub-Categories by Revenue")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=50))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        top_profit = prod.sort_values("Profit", ascending=False).head(10)
        fig = px.bar(top_profit, x="Profit", y="Sub_Category", color="Category", orientation="h",
                     title="Top 10 by Profit")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        worst = prod.sort_values("Profit", ascending=True).head(10)
        fig = px.bar(worst, x="Profit", y="Sub_Category", color="Category", orientation="h",
                     title="Lowest-Profit Sub-Categories")
        fig.update_layout(yaxis={"categoryorder": "total descending"}, margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Sales vs Profit (by Sub-Category)</div>', unsafe_allow_html=True)
    fig = px.scatter(prod, x="Revenue", y="Profit", color="Category", size="Orders",
                      hover_data=["Sub_Category", "Profit_Margin_Pct"],
                      title="Sales vs Profit — bubble size = order count")
    fig.update_layout(margin=dict(t=50))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Category / Sub-Category Performance Table</div>', unsafe_allow_html=True)
    st.dataframe(
        prod.sort_values("Revenue", ascending=False).style.format(
            {"Revenue": "₹{:,.0f}", "Profit": "₹{:,.0f}", "Profit_Margin_Pct": "{:.1f}%"}
        ),
        use_container_width=True,
    )


# =======================================================================
# TAB 3: CUSTOMER ANALYSIS
# =======================================================================
with page[2]:
    cust = (filtered.groupby(["Customer_ID", "Customer_Name"])
                     .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
                          Orders=("Order_ID", "nunique"))
                     .reset_index())

    orders_per_cust = cust["Orders"]
    repeat_rate = (orders_per_cust > 1).mean() * 100

    c1, c2, c3 = st.columns(3)
    kpi_card(c1, "Total Customers (in view)", f"{len(cust):,}")
    kpi_card(c2, "Repeat Customer Rate", f"{repeat_rate:.1f}%")
    kpi_card(c3, "Avg Revenue / Customer", f"₹{cust['Revenue'].mean():,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top 10 Customers by Revenue</div>', unsafe_allow_html=True)
    top_cust = cust.sort_values("Revenue", ascending=False).head(10)
    fig = px.bar(top_cust, x="Revenue", y="Customer_Name", orientation="h",
                 title="Top 10 Customers")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=50))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        repeat_flag = np.where(orders_per_cust.values > 1, "Repeat", "One-time")
        repeat_df = pd.DataFrame({"Type": repeat_flag}).value_counts().reset_index(name="Customers")
        fig = px.pie(repeat_df, names="Type", values="Customers", title="Repeat vs One-Time Customers",
                     hole=0.45)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.histogram(cust, x="Revenue", nbins=40, title="Customer Revenue Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">RFM Customer Segmentation</div>', unsafe_allow_html=True)
    rfm_in_view = rfm[rfm["Customer_ID"].isin(filtered["Customer_ID"].unique())]
    seg_summary = segment_summary(rfm_in_view)

    col3, col4 = st.columns(2)
    with col3:
        fig = px.pie(seg_summary, names="Segment", values="Customers",
                     title="Customers by Segment", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        fig = px.bar(seg_summary.sort_values("Total_Monetary", ascending=True),
                     x="Total_Monetary", y="Segment", orientation="h",
                     title="Revenue Contribution by Segment")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Segment definitions & recommended action:**")
    for seg in seg_summary["Segment"]:
        st.markdown(
            f'<div class="insight-box"><b>{seg}</b> — {SEGMENT_DESCRIPTIONS.get(seg, "")}</div>',
            unsafe_allow_html=True,
        )


# =======================================================================
# TAB 4: REGIONAL ANALYSIS
# =======================================================================
with page[3]:
    reg = (filtered.groupby("Region", observed=True)
                    .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
                         Orders=("Order_ID", "nunique"))
                    .assign(Profit_Margin_Pct=lambda x: (x["Profit"] / x["Revenue"] * 100).round(2))
                    .sort_values("Revenue", ascending=False)
                    .reset_index())

    best, worst = reg.iloc[0], reg.iloc[-1]
    c1, c2 = st.columns(2)
    kpi_card(c1, "Best-Performing Region", f"{best['Region']} (₹{best['Revenue']:,.0f})")
    kpi_card(c2, "Weakest Region", f"{worst['Region']} (₹{worst['Revenue']:,.0f})")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(reg, x="Region", y="Revenue", color="Region", title="Revenue by Region")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(reg, x="Region", y="Profit_Margin_Pct", color="Region",
                     title="Profit Margin % by Region")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Top Cities by Revenue</div>', unsafe_allow_html=True)
    city = (filtered.groupby(["Region", "City"], observed=True)["Sales"].sum()
                     .sort_values(ascending=False).head(15).reset_index())
    fig = px.bar(city, x="Sales", y="City", color="Region", orientation="h",
                 title="Top 15 Cities by Revenue")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        reg.style.format({"Revenue": "₹{:,.0f}", "Profit": "₹{:,.0f}", "Profit_Margin_Pct": "{:.1f}%"}),
        use_container_width=True,
    )


# =======================================================================
# TAB 5: INSIGHTS & ABOUT
# =======================================================================
with page[4]:
    st.markdown('<div class="section-title">🔑 Key Business Insights</div>', unsafe_allow_html=True)
    st.caption("Auto-generated from the currently filtered dataset — not hardcoded.")
    for ins in generate_insights(filtered):
        st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">✅ Business Recommendations</div>', unsafe_allow_html=True)
    recs = [
        "Reduce discounting on Electronics sub-categories (e.g. Laptops) — the data shows the "
        "steepest margin erosion is concentrated here, not spread evenly across categories.",
        "Prioritize retention offers for the 'At Risk' and 'Loyal Customer' RFM segments — they "
        "already generate high monetary value and are cheaper to retain than to reacquire.",
        "Investigate the weakest-performing region's product mix and marketing spend — its "
        "revenue gap versus the top region is large enough to warrant a dedicated review.",
        "Double down on high-margin, lower-revenue categories (Beauty & Personal Care, Fashion) "
        "with targeted promotion, since they already convert revenue to profit efficiently.",
        "Use the 'Champions' segment for referral and review programs before spending acquisition "
        "budget — they represent a disproportionate share of total profit.",
    ]
    for r in recs:
        st.markdown(f'<div class="insight-box">💡 {r}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">ℹ️ About This Project</div>', unsafe_allow_html=True)
    st.markdown(f"""
**Methodology:** A synthetic-but-realistic e-commerce orders dataset ({len(df):,} cleaned rows,
{df['Customer_ID'].nunique():,} unique customers, {df['Order_Date'].min().strftime('%b %Y')}
–{df['Order_Date'].max().strftime('%b %Y')}) was generated with built-in data-quality issues
(missing values, duplicates, mixed date formats, outliers) to mirror a real operational
dataset. It was cleaned with a reproducible Pandas pipeline (`src/data_cleaning.py`),
analyzed with Pandas/NumPy and SQL (`sql/analysis_queries.sql`), segmented with RFM analysis
(`src/rfm_analysis.py`), and visualized here with Streamlit + Plotly.

**Tech stack:** Python, Pandas, NumPy, SQLite/SQL, Streamlit, Plotly, Matplotlib/Seaborn (EDA notebook).

**Data last updated:** {df['Order_Date'].max().strftime('%d %B %Y')}
""")
