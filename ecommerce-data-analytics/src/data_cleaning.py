"""
data_cleaning.py
-----------------
Loads the raw e-commerce dataset and returns a cleaned DataFrame.

Cleaning steps performed (each one addresses a real issue injected into
the raw data — see src/generate_dataset.py for what was injected and why):

1. Parse Order_Date across mixed formats (YYYY-MM-DD and DD/MM/YYYY).
2. Drop exact duplicate rows (duplicate order submissions).
3. Standardize text columns: strip whitespace, fix inconsistent casing.
4. Handle missing values:
   - Discount  -> fill with 0 (no discount recorded = none applied)
   - City      -> fill with "Unknown"
   - Payment_Mode -> fill with the column mode (most common payment method)
5. Correct data types (numeric columns, category dtype for low-cardinality
   text columns to save memory).
6. Detect and cap extreme outliers in Sales using the IQR method (values
   are capped, not dropped, since they represent real high-value orders
   distorted by a data-entry style error, not orders to discard).
7. Feature engineering: Year, Month, Month_Name, Quarter, Profit_Margin,
   Revenue_per_Unit.

Run standalone:
    python src/data_cleaning.py
Output:
    Prints a before/after summary and writes data/ecommerce_clean.csv
"""

import numpy as np
import pandas as pd


def load_raw(path: str = "data/ecommerce.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    def _parse(value):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return pd.to_datetime(value, format=fmt)
            except (ValueError, TypeError):
                continue
        return pd.NaT

    df["Order_Date"] = df["Order_Date"].apply(_parse)
    return df


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    text_cols = ["Region", "City", "Category", "Sub_Category", "Payment_Mode",
                 "Customer_Name", "Product"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan})
    # Title-case Region/City so "NORTH" and "North" merge into one value
    df["Region"] = df["Region"].str.title()
    df["City"] = df["City"].str.title()
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df["Discount"] = df["Discount"].fillna(0.0)
    df["City"] = df["City"].fillna("Unknown")
    mode_payment = df["Payment_Mode"].mode(dropna=True)[0]
    df["Payment_Mode"] = df["Payment_Mode"].fillna(mode_payment)
    return df


def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").astype("Int64")
    df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce")
    for col in ["Region", "Category", "Sub_Category", "Payment_Mode"]:
        df[col] = df[col].astype("category")
    return df


def cap_outliers(df: pd.DataFrame, col: str = "Sales") -> pd.DataFrame:
    q1, q3 = df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_outliers = int(((df[col] < lower) | (df[col] > upper)).sum())
    df[col] = df[col].clip(lower=max(lower, 0), upper=upper)
    print(f"  Capped {n_outliers} outliers in '{col}' to range "
          f"[{max(lower, 0):.2f}, {upper:.2f}]")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df["Year"] = df["Order_Date"].dt.year
    df["Month"] = df["Order_Date"].dt.month
    df["Month_Name"] = df["Order_Date"].dt.strftime("%b")
    df["Quarter"] = df["Order_Date"].dt.quarter
    df["Year_Month"] = df["Order_Date"].dt.to_period("M").astype(str)
    df["Profit_Margin"] = np.where(df["Sales"] > 0, df["Profit"] / df["Sales"], 0)
    df["Revenue_per_Unit"] = np.where(df["Quantity"] > 0,
                                       df["Sales"] / df["Quantity"], df["Sales"])
    return df


def clean_pipeline(raw_path: str = "data/ecommerce.csv") -> pd.DataFrame:
    print("Loading raw data...")
    df = load_raw(raw_path)
    rows_before = len(df)

    print("Parsing dates (handles mixed date formats)...")
    df = parse_dates(df)

    print("Removing exact duplicate rows...")
    dupes = df.duplicated().sum()
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"  Removed {dupes} duplicate rows")

    print("Standardizing text columns...")
    df = clean_text_columns(df)

    print("Handling missing values...")
    missing_before = df.isna().sum()
    df = handle_missing_values(df)

    print("Fixing data types...")
    df = fix_dtypes(df)

    print("Detecting & capping outliers...")
    df = cap_outliers(df, "Sales")

    print("Engineering features (Year, Month, Profit_Margin, etc.)...")
    df = engineer_features(df)

    rows_after = len(df)
    print("\n--- Cleaning Summary ---")
    print(f"Rows before: {rows_before} | Rows after: {rows_after}")
    print("Missing values found (pre-clean):")
    print(missing_before[missing_before > 0])
    print(f"Final shape: {df.shape}")

    return df


if __name__ == "__main__":
    clean_df = clean_pipeline()
    clean_df.to_csv("data/ecommerce_clean.csv", index=False)
    print("\nSaved cleaned dataset -> data/ecommerce_clean.csv")
