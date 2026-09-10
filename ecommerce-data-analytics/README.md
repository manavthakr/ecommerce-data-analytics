# 🛒 E-Commerce Sales & Customer Analytics Dashboard

An end-to-end data analytics project that cleans a raw e-commerce orders
dataset, analyzes it with Python and SQL, segments customers using RFM
analysis, and presents everything in a live, interactive Streamlit
dashboard. Built to demonstrate the full workflow a junior/entry-level
Data Analyst is expected to own: **data cleaning → EDA → SQL → KPI &
segmentation analysis → dashboard → business recommendations.**

**🔗 Live Dashboard:** _add your deployed Streamlit Cloud URL here after deployment_

---

## 1. Business Problem

A mid-sized e-commerce company has order-level transaction data but no
consolidated way to answer basic-but-critical business questions:
Which categories/regions drive revenue vs. profit? Which products look
good on revenue but are quietly unprofitable? Which customers are worth
retaining, and which are already lost? This project builds the
analytics layer that answers those questions and turns them into
concrete recommendations.

## 2. Objectives

- Clean and validate a realistic, imperfect orders dataset
- Compute core business KPIs (revenue, profit, AOV, margin, repeat rate)
- Answer 10 real analytical questions in SQL
- Segment customers with RFM analysis
- Surface auto-generated (not hand-typed) insights and recommendations
- Ship all of it as a deployed, interactive dashboard

## 3. Dataset

`data/ecommerce.csv` — a synthetically generated but realistically
structured orders dataset (**12,004 cleaned rows**, originally 12,060
before deduplication, spanning **Jan 2023 – Dec 2025**, **2,166 unique
customers**). It was generated with `src/generate_dataset.py` using
category-specific pricing/margins, seasonal demand, and a Pareto-style
distribution of customer purchase frequency — then had realistic data
issues deliberately injected (missing values, duplicate rows,
inconsistent text casing, mixed date formats, and outlier sales values)
so the cleaning step is a genuine exercise, not a formality.

**Columns:** `Order_ID, Order_Date, Customer_ID, Customer_Name, Category,
Sub_Category, Product, Sales, Quantity, Discount, Profit, Region, City,
Payment_Mode` (+ engineered columns: `Year, Month, Month_Name, Quarter,
Year_Month, Profit_Margin, Revenue_per_Unit`).

> Why synthetic instead of a public dataset (e.g. Superstore)? Public
> e-commerce datasets are small and heavily reused, so they're
> instantly recognizable in interviews. This generator produces the
> same schema and business dynamics a real orders table would have,
> at a larger, less generic scale, while every metric below is still
> **computed from the data**, not invented.

## 4. Tech Stack

| Layer            | Tools |
|-------------------|-------|
| Data generation & cleaning | Python, Pandas, NumPy |
| EDA               | Jupyter Notebook, Matplotlib, Seaborn |
| Database & SQL    | SQLite (portable to PostgreSQL/MySQL) |
| Segmentation      | RFM Analysis (Pandas) |
| Dashboard         | Streamlit, Plotly |
| Deployment        | Streamlit Community Cloud |

## 5. Project Architecture

```
ecommerce-data-analytics/
│
├── data/
│   ├── ecommerce.csv            # raw synthetic dataset
│   ├── ecommerce_clean.csv      # cleaned dataset (generated)
│   └── rfm_segments.csv         # RFM output (generated)
│
├── notebooks/
│   └── EDA.ipynb                # full exploratory analysis, executed & saved
│
├── sql/
│   └── analysis_queries.sql     # 10 analytical questions + 1 bonus, tested against SQLite
│
├── src/
│   ├── generate_dataset.py      # synthetic dataset generator
│   ├── data_cleaning.py         # reusable cleaning pipeline
│   ├── analysis.py              # KPIs, trends, auto-generated insights
│   └── rfm_analysis.py          # RFM scoring & segmentation
│
├── app/
│   └── app.py                   # Streamlit dashboard (5 pages, live filters)
│
├── requirements.txt
├── README.md
└── .gitignore
```

`app/app.py`, the notebook, and the SQL layer all call the **same**
`src/data_cleaning.py` and `src/analysis.py` logic — so numbers never
drift between the notebook, the dashboard, and this README.

## 6. Data Cleaning Process

Implemented in `src/data_cleaning.py`, run via `clean_pipeline()`:

1. **Date parsing** across two mixed formats (`YYYY-MM-DD` and `DD/MM/YYYY`)
2. **Duplicate removal** — 56 exact duplicate rows dropped
3. **Text standardization** — trims whitespace, normalizes casing
   (e.g. `"NORTH"` → `"North"`)
4. **Missing value handling**:
   - `Discount` → filled with `0` (no discount recorded)
   - `City` → filled with `"Unknown"`
   - `Payment_Mode` → filled with the column mode
5. **Data type correction** — numeric coercion, `category` dtype for
   low-cardinality text columns
6. **Outlier handling** — IQR-based detection and capping on `Sales`
7. **Feature engineering** — `Year`, `Month`, `Quarter`, `Year_Month`,
   `Profit_Margin`, `Revenue_per_Unit`

**Result:** 12,060 → **12,004 rows**, 0 missing values remaining, 21 columns.

## 7. SQL Analysis

`sql/analysis_queries.sql` contains 10 analytical questions (plus a
bonus YoY growth query), covering `GROUP BY`, `JOIN`-ready structure,
`CASE`, **CTEs**, **window functions** (`RANK()`, `LAG()`), subqueries,
and date functions. Every query has been executed against
`data/ecommerce.db` (SQLite) to confirm it runs correctly. Questions
answered include: total sales/profit, monthly trend, revenue by
category, top products by profit, regional ranking, top customers by
lifetime value (CTE + `RANK()`), average order value, repeat customer
rate, discount-vs-margin relationship, and high-revenue/low-margin
products.

## 8. Key Business KPIs

*(Computed on the full cleaned dataset — the live dashboard recomputes these for whatever filters are applied.)*

| KPI | Value |
|---|---|
| Total Revenue | ₹14,32,99,694.55 |
| Total Profit | ₹1,54,14,624.35 |
| Overall Profit Margin | 10.76% |
| Total Orders | 12,000 |
| Average Order Value | ₹11,941.64 |
| Total Customers | 2,166 |
| Repeat Customer Rate | 64.91% |
| Avg. Customer Lifetime Value (profit-based approx.) | ₹7,116.63 |

## 9. Customer Segmentation (RFM)

Customers were scored on **Recency, Frequency, and Monetary** value
(quintile scoring) and mapped to segments:

| Segment | Customers | % of Customers | % of Revenue |
|---|---|---|---|
| Champions | 462 | 21.3% | 69.2% |
| Loyal Customers | 393 | 18.1% | 14.6% |
| At Risk | 210 | 9.7% | 7.1% |
| Needs Attention | 535 | 24.7% | 6.2% |
| Potential Loyalists | 159 | 7.3% | 1.6% |
| Lost Customers | 407 | 18.8% | 1.4% |

**Takeaway:** Champions are ~21% of customers but drive ~69% of
revenue — retention and loyalty investment should be concentrated
there and in "Loyal Customers" and "At Risk" (who are already
high-value but disengaging).

## 10. Dashboard Features

Built with Streamlit + Plotly (`app/app.py`), five pages:

- **Executive Overview** — KPI cards, monthly revenue/profit trend,
  sales & profit by category, sales by region
- **Product Analysis** — top/bottom sub-categories by revenue and
  profit, sales-vs-profit bubble chart, full performance table
- **Customer Analysis** — top customers, repeat vs. one-time split,
  revenue distribution, full RFM segmentation with action guidance
- **Regional Analysis** — region and city performance, best/worst
  region callouts
- **Insights & About** — auto-generated key insights, business
  recommendations, and project methodology

**Interactive filters** (sidebar, apply to every page): date range,
category, region, payment mode, and customer search.

## 11. Key Business Insights

*(Auto-generated by `src/analysis.py:generate_insights()` from the actual cleaned data — not hardcoded.)*

1. Electronics is the top revenue-generating category, contributing ₹8.07 crore (56.3% of total revenue).
2. Electronics also has the weakest profit margin at 6.7%, despite its revenue lead.
3. North is the strongest region by revenue (₹4.13 crore), while East underperforms at ₹2.66 crore.
4. Laptops (Electronics) generate above-median revenue but only a 5.7% profit margin — a pricing/discount review candidate.
5. Discount rate and profit margin show a negative correlation (r = -0.663) — higher discounts are associated with materially lower margins.
6. Oct 2024 was the strongest month (₹73.85 lakh revenue); Mar 2023 was the weakest (₹21.38 lakh).
7. Repeat customers are 64.9% of the base and are the main driver of long-term value (avg. lifetime profit ≈ ₹7,117/customer).

## 12. Business Recommendations

- **Reduce discounting on Electronics** (especially Laptops) — this is where margin erosion is steepest, not spread evenly across categories.
- **Prioritize retention for "Loyal Customers" and "At Risk" segments** — they already generate high value and are cheaper to retain than to reacquire.
- **Investigate the East region's underperformance** — its revenue gap versus North is large enough to warrant a dedicated review of assortment and marketing spend.
- **Promote high-margin categories** (Beauty & Personal Care at 29.2% margin, Fashion at 23.0%) more aggressively — they convert revenue to profit far more efficiently than Electronics.
- **Use "Champions" for referral/review programs** before spending acquisition budget — 21% of customers already drive 69% of revenue.

## 13. How to Run Locally

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd ecommerce-data-analytics

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Regenerate the dataset from scratch
python src/generate_dataset.py

# 5. Run the cleaning + analysis pipeline (also usable standalone)
python src/data_cleaning.py
python src/analysis.py
python src/rfm_analysis.py

# 6. Launch the dashboard
streamlit run app/app.py
```

The app will open at `http://localhost:8501`. If `data/ecommerce_clean.csv`
doesn't exist yet, `app.py` will clean the raw data automatically on
first load.

## 14. Deployment (Streamlit Community Cloud)

1. **Create a GitHub repository** and push this project (make sure
   `data/ecommerce.csv` is committed — `.gitignore` excludes only the
   generated DB/JSON files, not the source dataset).
2. **Go to** [share.streamlit.io](https://share.streamlit.io) and sign
   in with GitHub.
3. Click **"New app"**, select your repository, branch (`main`), and
   set the **main file path** to `app/app.py`.
4. Streamlit Cloud will read `requirements.txt` automatically and
   install dependencies — no extra configuration needed.
5. Click **Deploy**. First build typically takes 2–5 minutes.
6. Once live, copy the generated URL (e.g.
   `https://<your-app-name>.streamlit.app`) and add it to the top of
   this README and to your resume/portfolio links.
7. **Verify:** open the URL, confirm all 5 tabs load and filters update
   the charts. If it fails, see Troubleshooting below.

No paid services are required.

## 15. Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError` on deploy | Confirm the missing package is listed in `requirements.txt` with a version floor, then reboot the app from the Streamlit Cloud dashboard. |
| App builds but shows a blank page | Check the Streamlit Cloud "Manage app" logs — usually a path issue; confirm `data/ecommerce.csv` was actually committed to the repo. |
| `FileNotFoundError` for the dataset | Scripts assume they're run from the project root (paths are relative to `data/`). Run commands from the repo root, not from inside `src/`. |
| Notebook cells fail on `from data_cleaning import ...` | The notebook adds `../src` to `sys.path` — make sure you're running it from within `notebooks/`, not after moving the file. |
| Charts don't update when filters change | Confirm you're on the deployed/updated version — `st.cache_data` caches the *raw load*, not the filtered views, so filters should always be live. |

## 16. Future Improvements

- Add cohort-based retention analysis (month-of-first-purchase cohorts)
- Add a simple demand-forecasting model (e.g. Prophet) for next-quarter revenue
- Add CSV upload so the dashboard works on any company's own order data
- Add authentication if this were to hold real (non-synthetic) customer data
- Migrate the SQL layer to PostgreSQL for a cloud-hosted, multi-user backend

---

## Resume Content

### Resume Project Title
**E-Commerce Sales & Customer Analytics Dashboard**

### Resume Bullet Points

- Engineered an end-to-end analytics pipeline in Python (Pandas, NumPy) to clean and process 12,000+ e-commerce transactions, resolving missing values, duplicates, and outliers to produce an analysis-ready dataset.
- Wrote 10+ SQL queries using CTEs, window functions, and subqueries against a SQLite database to answer revenue, profitability, and customer lifetime value questions for business stakeholders.
- Built and deployed an interactive Streamlit + Plotly dashboard with RFM-based customer segmentation, live filters, and auto-generated insights, enabling data-driven identification of a 64.9% repeat-customer base and a -0.66 discount-to-margin correlation.

---

## Interview Preparation — 15 Questions & Answers

**1. Why did you use Pandas for cleaning instead of doing it in SQL?**
Pandas gives finer control for row-level logic like parsing two
different date formats or applying custom outlier-capping rules,
and it's easy to unit-test and reuse across the notebook, SQL-loading
script, and dashboard from one function (`clean_pipeline()`). SQL is
better once the data is already tidy and you're aggregating.

**2. How did you handle missing values, and why those specific strategies?**
Each column got a strategy matching its meaning: `Discount` missing
almost certainly means "no discount applied," so it's filled with 0.
`City` is filled with `"Unknown"` rather than dropped, since dropping
would lose the whole order's revenue/profit data just because a
delivery city wasn't logged. `Payment_Mode` is filled with the mode
(most common payment method) since it's a low-impact categorical value.

**3. How did you detect and handle outliers?**
Using the IQR method: outliers are values below `Q1 - 1.5*IQR` or
above `Q3 + 1.5*IQR`. Instead of dropping them (which would remove
real high-value orders), I capped them at the IQR boundary, preserving
the row but preventing a few extreme values from distorting sums and averages.

**4. Walk me through your RFM segmentation.**
For each customer I calculate Recency (days since last order),
Frequency (distinct order count), and Monetary value (total revenue).
Each metric is scored 1-5 using quintiles, then the three scores are
combined with a rule-based mapping into segments like Champions, Loyal
Customers, At Risk, and Lost Customers — a standard, explainable
approach used broadly in retail/e-commerce.

**5. Why quintiles instead of fixed thresholds for RFM scoring?**
Quintiles adapt to the actual distribution of the data, so each score
band always contains roughly 20% of customers regardless of the
underlying scale. Fixed thresholds would need re-tuning any time order
volume or spend levels change.

**6. What's the difference between Recency, Frequency, and Monetary in your model?**
Recency = how recently they last ordered (lower is better). Frequency
= how many distinct orders they've placed (higher is better).
Monetary = total revenue they've generated (higher is better). Recency
score is inverted in scoring since fewer days-since-last-order is the
"good" direction.

**7. How did you calculate Customer Lifetime Value here?**
I used a simple historical approximation: total profit generated per
customer over the dataset's timeframe, averaged across all customers.
It's not a predictive CLV model (which would project future value),
but it's a defensible, data-grounded proxy appropriate for this scope.

**8. Explain the SQL query you're most proud of.**
The top-customers query uses a CTE to first aggregate each customer's
total spend and profit, then applies a window function (`RANK()`) over
that aggregated result to rank customers — this avoids a messier
nested subquery and keeps the logic readable in two clear stages.

**9. How would you find customers with high sales but low profit using SQL?**
Group by category/sub-category, compute revenue and profit-margin per
group, then filter using `HAVING` against a subquery that calculates
the average sub-category revenue — flagging groups that are
above-average revenue but end up with poor margin.

**10. What does the discount-vs-profit-margin correlation of -0.663 tell you?**
It's a fairly strong negative correlation: as discount percentage
increases, profit margin tends to decrease. That's expected
directionally, but the strength of it (r = -0.663, not just weakly
negative) suggests discounting is a meaningful lever management should
control more tightly rather than something with negligible cost.

**11. How would you explain "Average Order Value" and why it matters to a non-technical stakeholder?**
AOV is total revenue divided by number of distinct orders — basically
"how much does a typical order bring in." It matters because
increasing AOV (through upsells/bundling) is often cheaper than
acquiring new customers to hit the same revenue target.

**12. Why did you choose Streamlit over building this in Power BI/Tableau?**
Streamlit lets the whole project — data pipeline, SQL, and dashboard —
live in one Python codebase that's version-controlled, free to deploy,
and easy to explain end-to-end in an interview, versus a BI tool that
would sit separately from the analysis code.

**13. How does your dashboard stay fast when filters change?**
The raw data load is cached with `st.cache_data` so it's read from
disk once per session, not on every filter change. All filtering and
aggregation happens on the already-loaded DataFrame in memory, which
is fast even at tens of thousands of rows.

**14. What would break if this dataset had millions of rows instead of 12,000?**
Pandas would start to strain on memory and the Streamlit app would get
slower on each filter change. At that scale I'd move aggregation into
the SQL layer (or a warehouse like BigQuery/Snowflake) and have the
dashboard query pre-aggregated summary tables instead of raw
transaction-level data.

**15. How did you deploy this, and what would you change for a production system?**
It's deployed on Streamlit Community Cloud directly from GitHub — free,
simple, no infrastructure to manage, which fits a portfolio project. For
a real production system I'd add authentication, move the data to a
managed database instead of a flat CSV/SQLite file, add scheduled data
refresh, and add monitoring/logging for the app itself.
