"""
rfm_analysis.py
----------------
Recency, Frequency, Monetary (RFM) customer segmentation.

Method:
1. For each customer compute:
   - Recency:   days since their most recent order (relative to the
                dataset's max order date, used as "today")
   - Frequency: number of distinct orders
   - Monetary:  total revenue (Sales) contributed
2. Score each metric 1-5 using quintiles (5 = best: most recent,
   most frequent, highest spend).
3. Combine the three scores into a segment using a standard RFM rule set.

Run standalone:
    python src/rfm_analysis.py
Output:
    Prints segment counts/revenue share, writes data/rfm_segments.csv
"""

import numpy as np
import pandas as pd
from data_cleaning import clean_pipeline


def calculate_rfm(df: pd.DataFrame) -> pd.DataFrame:
    snapshot_date = df["Order_Date"].max() + pd.Timedelta(days=1)

    rfm = (df.groupby("Customer_ID")
             .agg(
                 Recency=("Order_Date", lambda x: (snapshot_date - x.max()).days),
                 Frequency=("Order_ID", "nunique"),
                 Monetary=("Sales", "sum"),
             )
             .reset_index())

    # Quintile scores. Recency is inverted (lower days = better = score 5).
    rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5,
                              labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["RFM_Score"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)
    rfm["RFM_Total"] = rfm[["R_Score", "F_Score", "M_Score"]].sum(axis=1)

    rfm["Segment"] = rfm.apply(assign_segment, axis=1)
    return rfm


def assign_segment(row) -> str:
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "Potential Loyalists"
    if r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    if r <= 2 and f <= 2 and m <= 2:
        return "Lost Customers"
    return "Needs Attention"


SEGMENT_DESCRIPTIONS = {
    "Champions": "Bought recently, buy often, and spend the most. Reward them — "
                 "early access, loyalty perks — and use them for referrals/reviews.",
    "Loyal Customers": "Consistent purchasers with solid spend. Upsell higher-value "
                        "products and keep them engaged with regular communication.",
    "Potential Loyalists": "Recent customers who haven't purchased often yet. "
                            "Nurture with onboarding offers and category recommendations "
                            "to build a repeat habit.",
    "At Risk": "Used to purchase frequently/high-value but haven't ordered recently. "
               "Win back with targeted, personalized re-engagement offers before they churn.",
    "Lost Customers": "Low recency, frequency, and monetary value. Low-cost win-back "
                       "campaigns only; not a priority for active investment.",
    "Needs Attention": "Below-average across the board but not yet lost. Monitor and "
                        "nudge with moderate-value offers.",
}


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    out = (rfm.groupby("Segment")
              .agg(Customers=("Customer_ID", "count"),
                   Avg_Recency_Days=("Recency", "mean"),
                   Avg_Frequency=("Frequency", "mean"),
                   Total_Monetary=("Monetary", "sum"))
              .assign(Pct_of_Customers=lambda x: (x["Customers"] / x["Customers"].sum() * 100).round(1),
                      Pct_of_Revenue=lambda x: (x["Total_Monetary"] / x["Total_Monetary"].sum() * 100).round(1))
              .sort_values("Total_Monetary", ascending=False)
              .reset_index())
    return out


if __name__ == "__main__":
    df = clean_pipeline()
    rfm = calculate_rfm(df)

    print("\n=== RFM Segment Summary ===")
    summary = segment_summary(rfm)
    print(summary.to_string(index=False))

    print("\n=== Segment Descriptions ===")
    for seg, desc in SEGMENT_DESCRIPTIONS.items():
        if seg in rfm["Segment"].values:
            print(f"\n{seg}:\n  {desc}")

    rfm.to_csv("data/rfm_segments.csv", index=False)
    print("\nSaved -> data/rfm_segments.csv")
