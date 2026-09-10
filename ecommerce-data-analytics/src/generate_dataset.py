"""
generate_dataset.py
--------------------
Generates a realistic synthetic e-commerce orders dataset for the
E-Commerce Sales & Customer Analytics Dashboard project.

Why synthetic (and why it's still realistic):
- Public e-commerce datasets (like the classic "Superstore" dataset) are
  small (~10k rows) and heavily reused, which stands out in interviews.
- This generator builds a dataset with the SAME schema and business logic
  a real retailer's order table would have: seasonality, category-specific
  margins, discount effects on profit, repeat customers, regional skew,
  and realistic noise/outliers/missing values that require genuine
  cleaning (not just a "run .dropna() and move on" exercise).
- Every downstream number in the README/insights is computed FROM this
  file, not invented.

Run:
    python src/generate_dataset.py
Output:
    data/ecommerce.csv  (~12,000 rows)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG = np.random.default_rng(42)
N_ORDERS = 12000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)

# ---------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------
CATEGORIES = {
    "Electronics": {
        "sub": ["Smartphones", "Laptops", "Headphones", "Cameras", "Accessories"],
        "price_range": (800, 60000),
        "base_margin": 0.14,
    },
    "Fashion": {
        "sub": ["Men's Wear", "Women's Wear", "Footwear", "Watches", "Bags"],
        "price_range": (300, 6000),
        "base_margin": 0.32,
    },
    "Home & Kitchen": {
        "sub": ["Furniture", "Cookware", "Decor", "Appliances", "Storage"],
        "price_range": (400, 25000),
        "base_margin": 0.22,
    },
    "Beauty & Personal Care": {
        "sub": ["Skincare", "Haircare", "Makeup", "Fragrance", "Grooming"],
        "price_range": (150, 3500),
        "base_margin": 0.38,
    },
    "Sports & Outdoors": {
        "sub": ["Fitness Equipment", "Cycling", "Camping", "Sportswear", "Yoga"],
        "price_range": (250, 15000),
        "base_margin": 0.20,
    },
    "Books & Stationery": {
        "sub": ["Fiction", "Non-Fiction", "Academic", "Office Supplies", "Art Supplies"],
        "price_range": (99, 2500),
        "base_margin": 0.18,
    },
}

REGIONS = {
    "North": ["Delhi", "Chandigarh", "Lucknow", "Jaipur"],
    "South": ["Bengaluru", "Chennai", "Hyderabad", "Kochi"],
    "West": ["Mumbai", "Pune", "Ahmedabad", "Surat"],
    "East": ["Kolkata", "Bhubaneswar", "Patna", "Guwahati"],
}

PAYMENT_MODES = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery"]
PAYMENT_WEIGHTS = [0.22, 0.15, 0.38, 0.10, 0.15]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
               "Ananya", "Diya", "Ishita", "Priya", "Kavya", "Meera", "Riya", "Sneha",
               "Rohan", "Karan", "Nikhil", "Aman", "Pooja", "Neha", "Simran", "Tanya"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Reddy", "Iyer",
              "Nair", "Menon", "Chatterjee", "Bose", "Malhotra", "Kapoor", "Joshi", "Das"]

# Fixed pool of customers so repeat purchases / RFM / CLV are meaningful
N_CUSTOMERS = 3200
customer_ids = [f"CUST-{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
customer_names = [f"{RNG.choice(FIRST_NAMES)} {RNG.choice(LAST_NAMES)}" for _ in range(N_CUSTOMERS)]
customer_name_map = dict(zip(customer_ids, customer_names))

# Give customers unequal purchase propensity (some are frequent, most aren't) -> Pareto-like
propensity = RNG.pareto(1.5, N_CUSTOMERS) + 0.1
propensity = propensity / propensity.sum()

# Assign each customer a home region (keeps region/customer patterns coherent)
customer_region = {cid: RNG.choice(list(REGIONS.keys()), p=[0.30, 0.28, 0.24, 0.18])
                    for cid in customer_ids}


def random_date():
    """Seasonal date sampling: boosts Oct-Jan (festive/holiday season)."""
    total_days = (END_DATE - START_DATE).days
    day_offset = RNG.integers(0, total_days)
    date = START_DATE + timedelta(days=int(day_offset))
    # Reweight toward festive months by resampling with small probability
    if date.month not in (10, 11, 12, 1) and RNG.random() < 0.35:
        day_offset = RNG.integers(0, total_days)
        candidate = START_DATE + timedelta(days=int(day_offset))
        tries = 0
        while candidate.month not in (10, 11, 12, 1) and tries < 5:
            day_offset = RNG.integers(0, total_days)
            candidate = START_DATE + timedelta(days=int(day_offset))
            tries += 1
        date = candidate
    return date


rows = []
for order_num in range(1, N_ORDERS + 1):
    order_id = f"ORD-{order_num:06d}"

    customer_id = RNG.choice(customer_ids, p=propensity)
    customer_name = customer_name_map[customer_id]

    category = RNG.choice(list(CATEGORIES.keys()), p=[0.24, 0.22, 0.18, 0.16, 0.12, 0.08])
    cat_info = CATEGORIES[category]
    sub_category = RNG.choice(cat_info["sub"])

    region = customer_region[customer_id]
    # Small chance customer orders while traveling / gifting to another region
    if RNG.random() < 0.08:
        region = RNG.choice(list(REGIONS.keys()))
    city = RNG.choice(REGIONS[region])

    order_date = random_date()

    quantity = int(RNG.choice([1, 1, 1, 2, 2, 3, 4], p=[0.42, 0.001, 0.409, 0.08, 0.05, 0.03, 0.01]))
    # (weights above sum≈1; keep simple)
    unit_price = RNG.uniform(*cat_info["price_range"])
    sales = round(unit_price * quantity, 2)

    # Discount: promo-driven, higher on Electronics/Home, occasional deep discounts
    base_discount = RNG.choice([0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40],
                                p=[0.30, 0.20, 0.18, 0.14, 0.10, 0.06, 0.02])
    discount = round(base_discount, 2)

    # Profit: category base margin, eroded by discount, plus noise; can go negative
    margin = cat_info["base_margin"] - (discount * 0.9) + RNG.normal(0, 0.04)
    profit = round(sales * margin, 2)

    payment_mode = RNG.choice(PAYMENT_MODES, p=PAYMENT_WEIGHTS)

    rows.append({
        "Order_ID": order_id,
        "Order_Date": order_date.strftime("%Y-%m-%d"),
        "Customer_ID": customer_id,
        "Customer_Name": customer_name,
        "Category": category,
        "Sub_Category": sub_category,
        "Product": f"{sub_category} - {RNG.integers(100, 999)}",
        "Sales": sales,
        "Quantity": quantity,
        "Discount": discount,
        "Profit": profit,
        "Region": region,
        "City": city,
        "Payment_Mode": payment_mode,
    })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------------
# Inject realistic data-quality issues (so cleaning is a genuine step)
# ---------------------------------------------------------------------
# 1) Missing values in a few columns
for col, frac in [("Discount", 0.02), ("City", 0.015), ("Payment_Mode", 0.01)]:
    idx = RNG.choice(df.index, size=int(len(df) * frac), replace=False)
    df.loc[idx, col] = np.nan

# 2) Duplicate rows (simulate double-submitted orders)
dupe_idx = RNG.choice(df.index, size=60, replace=False)
df = pd.concat([df, df.loc[dupe_idx]], ignore_index=True)

# 3) Inconsistent text casing / whitespace (common real-world mess)
messy_idx = RNG.choice(df.index, size=200, replace=False)
df.loc[messy_idx, "Region"] = df.loc[messy_idx, "Region"].str.upper()
messy_idx2 = RNG.choice(df.index, size=150, replace=False)
df.loc[messy_idx2, "City"] = " " + df.loc[messy_idx2, "City"].astype(str) + "  "

# 4) A few extreme outliers in Sales (data-entry style errors, e.g. missing decimal)
outlier_idx = RNG.choice(df.index, size=15, replace=False)
df.loc[outlier_idx, "Sales"] = df.loc[outlier_idx, "Sales"] * 100

# 5) Order_Date stored inconsistently for a handful of rows
messy_date_idx = RNG.choice(df.index, size=40, replace=False)
df.loc[messy_date_idx, "Order_Date"] = pd.to_datetime(
    df.loc[messy_date_idx, "Order_Date"]
).dt.strftime("%d/%m/%Y")

# Shuffle rows so injected issues aren't clustered at the end
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

df.to_csv("data/ecommerce.csv", index=False)
print(f"Generated {len(df)} rows -> data/ecommerce.csv")
