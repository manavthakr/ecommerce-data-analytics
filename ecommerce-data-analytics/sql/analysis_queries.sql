-- =====================================================================
-- analysis_queries.sql
-- E-Commerce Sales & Customer Analytics — SQL Analysis
-- Target: SQLite (data/ecommerce.db, table: orders)
-- Also portable to PostgreSQL/MySQL with minor date-function changes
-- (noted inline where relevant).
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Total Sales and Profit
-- ---------------------------------------------------------------------
SELECT
    ROUND(SUM(Sales), 2)   AS total_revenue,
    ROUND(SUM(Profit), 2)  AS total_profit,
    ROUND(SUM(Profit) * 100.0 / SUM(Sales), 2) AS overall_profit_margin_pct
FROM orders;


-- ---------------------------------------------------------------------
-- 2. Monthly Sales Trend
-- ---------------------------------------------------------------------
SELECT
    Year_Month,
    ROUND(SUM(Sales), 2)  AS monthly_revenue,
    ROUND(SUM(Profit), 2) AS monthly_profit,
    COUNT(DISTINCT Order_ID) AS orders
FROM orders
GROUP BY Year_Month
ORDER BY Year_Month;


-- ---------------------------------------------------------------------
-- 3. Revenue by Category (highest revenue first)
-- ---------------------------------------------------------------------
SELECT
    Category,
    ROUND(SUM(Sales), 2)  AS total_revenue,
    ROUND(SUM(Profit), 2) AS total_profit,
    ROUND(SUM(Profit) * 100.0 / SUM(Sales), 2) AS profit_margin_pct,
    COUNT(DISTINCT Order_ID) AS orders
FROM orders
GROUP BY Category
ORDER BY total_revenue DESC;


-- ---------------------------------------------------------------------
-- 4. Top 10 Products (Sub-Category) by Profit
-- ---------------------------------------------------------------------
SELECT
    Category,
    Sub_Category,
    ROUND(SUM(Profit), 2) AS total_profit,
    ROUND(SUM(Sales), 2)  AS total_revenue
FROM orders
GROUP BY Category, Sub_Category
ORDER BY total_profit DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- 5. Regional Performance, ranked
-- ---------------------------------------------------------------------
SELECT
    Region,
    ROUND(SUM(Sales), 2)  AS total_revenue,
    ROUND(SUM(Profit), 2) AS total_profit,
    RANK() OVER (ORDER BY SUM(Sales) DESC) AS revenue_rank
FROM orders
GROUP BY Region;


-- ---------------------------------------------------------------------
-- 6. Top 10 Customers by Lifetime Value (CTE + window function)
-- ---------------------------------------------------------------------
WITH customer_value AS (
    SELECT
        Customer_ID,
        Customer_Name,
        COUNT(DISTINCT Order_ID) AS total_orders,
        ROUND(SUM(Sales), 2)     AS total_spent,
        ROUND(SUM(Profit), 2)    AS total_profit_generated
    FROM orders
    GROUP BY Customer_ID, Customer_Name
)
SELECT
    Customer_ID,
    Customer_Name,
    total_orders,
    total_spent,
    total_profit_generated,
    RANK() OVER (ORDER BY total_spent DESC) AS spend_rank
FROM customer_value
ORDER BY total_spent DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- 7. Average Order Value (overall and by category)
-- ---------------------------------------------------------------------
-- Overall
SELECT ROUND(SUM(Sales) * 1.0 / COUNT(DISTINCT Order_ID), 2) AS avg_order_value
FROM orders;

-- By category
SELECT
    Category,
    ROUND(SUM(Sales) * 1.0 / COUNT(DISTINCT Order_ID), 2) AS avg_order_value
FROM orders
GROUP BY Category
ORDER BY avg_order_value DESC;


-- ---------------------------------------------------------------------
-- 8. Repeat Customer Rate
-- ---------------------------------------------------------------------
WITH order_counts AS (
    SELECT Customer_ID, COUNT(DISTINCT Order_ID) AS orders
    FROM orders
    GROUP BY Customer_ID
)
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS repeat_rate_pct
FROM order_counts;


-- ---------------------------------------------------------------------
-- 9. Discount vs Profit Margin (does higher discount correlate with
--    lower profit?) — bucketed CASE analysis (a full Pearson correlation
--    is computed in Python. SQL shows the pattern via discount bands)
-- ---------------------------------------------------------------------
SELECT
    CASE
        WHEN Discount = 0 THEN '0% (No Discount)'
        WHEN Discount <= 0.10 THEN '1-10%'
        WHEN Discount <= 0.20 THEN '11-20%'
        WHEN Discount <= 0.30 THEN '21-30%'
        ELSE '30%+'
    END AS discount_band,
    COUNT(*) AS orders,
    ROUND(AVG(Profit_Margin) * 100, 2) AS avg_profit_margin_pct
FROM orders
GROUP BY discount_band
ORDER BY MIN(Discount);


-- ---------------------------------------------------------------------
-- 10. High Sales but Low Profit Margin Products (below-average margin,
--     above-median revenue) — subquery for the revenue threshold
-- ---------------------------------------------------------------------
SELECT
    Category,
    Sub_Category,
    ROUND(SUM(Sales), 2)  AS total_revenue,
    ROUND(SUM(Profit) * 100.0 / SUM(Sales), 2) AS profit_margin_pct
FROM orders
GROUP BY Category, Sub_Category
HAVING total_revenue > (
    SELECT AVG(sub_revenue) FROM (
        SELECT SUM(Sales) AS sub_revenue
        FROM orders
        GROUP BY Category, Sub_Category
    )
)
ORDER BY profit_margin_pct ASC
LIMIT 10;


-- ---------------------------------------------------------------------
-- Bonus: Year-over-Year revenue growth using window function LAG()
-- ---------------------------------------------------------------------
WITH yearly AS (
    SELECT Year, ROUND(SUM(Sales), 2) AS revenue
    FROM orders
    GROUP BY Year
)
SELECT
    Year,
    revenue,
    LAG(revenue) OVER (ORDER BY Year) AS prev_year_revenue,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY Year)) * 100.0
          / LAG(revenue) OVER (ORDER BY Year), 2) AS yoy_growth_pct
FROM yearly
ORDER BY Year;
