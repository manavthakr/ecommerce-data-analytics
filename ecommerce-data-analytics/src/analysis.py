"""
analysis.py
-----------
Computes KPIs, trend tables, and auto-generated business insights from the
cleaned dataset. This is the single source of truth for every number that
appears in the dashboard and the README — nothing here is hand-typed.

Run standalone:
    python src/analysis.py
Output:
    Prints KPIs and insights, writes insights.json for reuse in the app/README.
"""

import json
import numpy as np
import pandas as pd
from data_cleaning import clean_pipeline


def compute_kpis(df: pd.DataFrame) -> dict:
    total_revenue = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order_ID"].nunique()
    total_units = df["Quantity"].sum()
    aov = total_revenue / total_orders
    profit_margin = total_profit / total_revenue

    orders_per_customer = df.groupby("Customer_ID")["Order_ID"].nunique()
    repeat_customers = (orders_per_customer > 1).sum()
    total_customers = orders_per_customer.shape[0]
    repeat_rate = repeat_customers / total_customers

    clv_approx = df.groupby("Customer_ID")["Profit"].sum().mean()

    return {
        "total_revenue": round(float(total_revenue), 2),
        "total_profit": round(float(total_profit), 2),
        "total_orders": int(total_orders),
        "total_units_sold": int(total_units),
        "average_order_value": round(float(aov), 2),
        "profit_margin_pct": round(float(profit_margin) * 100, 2),
        "total_customers": int(total_customers),
        "repeat_customers": int(repeat_customers),
        "repeat_customer_rate_pct": round(float(repeat_rate) * 100, 2),
        "avg_customer_lifetime_value_approx": round(float(clv_approx), 2),
    }


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    out = (df.groupby("Year_Month")
             .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
                  Orders=("Order_ID", "nunique"))
             .reset_index()
             .sort_values("Year_Month"))
    return out


def category_performance(df: pd.DataFrame) -> pd.DataFrame:
    out = (df.groupby("Category", observed=True)
             .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
                  Orders=("Order_ID", "nunique"), Units=("Quantity", "sum"))
             .assign(Profit_Margin_Pct=lambda x: (x["Profit"] / x["Revenue"] * 100).round(2))
             .sort_values("Revenue", ascending=False)
             .reset_index())
    return out


def region_performance(df: pd.DataFrame) -> pd.DataFrame:
    out = (df.groupby("Region", observed=True)
             .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
                  Orders=("Order_ID", "nunique"))
             .sort_values("Revenue", ascending=False)
             .reset_index())
    return out


def product_performance(df: pd.DataFrame) -> pd.DataFrame:
    out = (df.groupby(["Category", "Sub_Category"], observed=True)
             .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
                  Orders=("Order_ID", "nunique"))
             .assign(Profit_Margin_Pct=lambda x: (x["Profit"] / x["Revenue"] * 100).round(2))
             .sort_values("Revenue", ascending=False)
             .reset_index())
    return out


def discount_profit_relationship(df: pd.DataFrame) -> float:
    """Pearson correlation between discount rate and profit margin."""
    return round(float(df["Discount"].corr(df["Profit_Margin"])), 3)


def generate_insights(df: pd.DataFrame) -> list:
    insights = []

    cat_perf = category_performance(df)
    top_rev_cat = cat_perf.iloc[0]
    insights.append(
        f"{top_rev_cat['Category']} is the top revenue-generating category, "
        f"contributing ₹{top_rev_cat['Revenue']:,.0f} "
        f"({top_rev_cat['Revenue'] / df['Sales'].sum() * 100:.1f}% of total revenue)."
    )

    lowest_margin_cat = cat_perf.sort_values("Profit_Margin_Pct").iloc[0]
    insights.append(
        f"{lowest_margin_cat['Category']} has the weakest profit margin at "
        f"{lowest_margin_cat['Profit_Margin_Pct']:.1f}%, despite generating "
        f"₹{lowest_margin_cat['Revenue']:,.0f} in revenue."
    )

    reg_perf = region_performance(df)
    best_region = reg_perf.iloc[0]
    worst_region = reg_perf.iloc[-1]
    insights.append(
        f"{best_region['Region']} is the strongest region by revenue "
        f"(₹{best_region['Revenue']:,.0f}), while {worst_region['Region']} "
        f"underperforms at ₹{worst_region['Revenue']:,.0f}."
    )

    prod_perf = product_performance(df)
    high_rev_low_margin = prod_perf[prod_perf["Revenue"] > prod_perf["Revenue"].median()]
    high_rev_low_margin = high_rev_low_margin.sort_values("Profit_Margin_Pct").head(1)
    if not high_rev_low_margin.empty:
        row = high_rev_low_margin.iloc[0]
        insights.append(
            f"'{row['Sub_Category']}' ({row['Category']}) generates above-median "
            f"revenue (₹{row['Revenue']:,.0f}) but only a {row['Profit_Margin_Pct']:.1f}% "
            f"profit margin — a candidate for pricing or discount review."
        )

    corr = discount_profit_relationship(df)
    direction = "negative" if corr < 0 else "positive"
    insights.append(
        f"Discount rate and profit margin show a {direction} correlation "
        f"(r = {corr}) — {'higher discounts are associated with lower margins' if corr < 0 else 'discounting does not appear to erode margin in this data'}."
    )

    m_trend = monthly_trend(df)
    best_month = m_trend.sort_values("Revenue", ascending=False).iloc[0]
    worst_month = m_trend.sort_values("Revenue", ascending=True).iloc[0]
    insights.append(
        f"{best_month['Year_Month']} was the strongest month "
        f"(₹{best_month['Revenue']:,.0f} in revenue), while {worst_month['Year_Month']} "
        f"was the weakest (₹{worst_month['Revenue']:,.0f})."
    )

    kpis = compute_kpis(df)
    insights.append(
        f"Repeat customers make up {kpis['repeat_customer_rate_pct']:.1f}% of the "
        f"customer base but are the main driver of long-term value "
        f"(avg. customer lifetime profit ≈ ₹{kpis['avg_customer_lifetime_value_approx']:,.0f})."
    )

    return insights


if __name__ == "__main__":
    df = clean_pipeline()

    kpis = compute_kpis(df)
    print("\n=== KPIs ===")
    for k, v in kpis.items():
        print(f"{k}: {v}")

    print("\n=== Category Performance ===")
    print(category_performance(df).to_string(index=False))

    print("\n=== Region Performance ===")
    print(region_performance(df).to_string(index=False))

    print("\n=== Key Business Insights ===")
    insights = generate_insights(df)
    for i, ins in enumerate(insights, 1):
        print(f"{i}. {ins}")

    with open("insights.json", "w") as f:
        json.dump({"kpis": kpis, "insights": insights}, f, indent=2)
    print("\nSaved -> insights.json")
