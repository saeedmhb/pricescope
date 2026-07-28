-- Day 1 solutions (Snowflake-flavored; notes where syntax differs elsewhere)

-- 1. Revenue per category
SELECT p.category, ROUND(SUM(s.units_sold * s.unit_price), 2) AS revenue
FROM pos_sales s JOIN products p USING (product_id)
GROUP BY p.category
ORDER BY revenue DESC;

-- 2. Distinct products per store, March 2025
SELECT store_id, COUNT(DISTINCT product_id) AS active_products
FROM pos_sales
WHERE sale_date BETWEEN '2025-03-01' AND '2025-03-31'
GROUP BY store_id
ORDER BY active_products ASC
LIMIT 5;

-- 3. Avg price promo vs non-promo per category (conditional aggregation)
SELECT p.category,
       AVG(CASE WHEN s.promo_flag = 0 THEN s.unit_price END) AS avg_price_regular,
       AVG(CASE WHEN s.promo_flag = 1 THEN s.unit_price END) AS avg_price_promo
FROM pos_sales s JOIN products p USING (product_id)
GROUP BY p.category;

-- 4. Revenue per region per month + % of total
WITH monthly AS (
  SELECT st.region, DATE_TRUNC('month', s.sale_date) AS month,
         SUM(s.units_sold * s.unit_price) AS revenue
  FROM pos_sales s JOIN stores st USING (store_id)
  GROUP BY st.region, DATE_TRUNC('month', s.sale_date)
)
SELECT region, month, ROUND(revenue, 2) AS revenue,
       ROUND(100 * revenue / SUM(revenue) OVER (PARTITION BY month), 1) AS pct_of_month
FROM monthly
ORDER BY month, region;

-- 5. Sold in 2024, never in 2026 (anti-join)
SELECT DISTINCT s24.product_id
FROM pos_sales s24
WHERE YEAR(s24.sale_date) = 2024
  AND NOT EXISTS (
    SELECT 1 FROM pos_sales s26
    WHERE s26.product_id = s24.product_id AND YEAR(s26.sale_date) = 2026
  );

-- 6. Promo uplift: units in promo window vs 4 weeks before
WITH promo_units AS (
  SELECT pr.promo_id, pr.product_id, pr.discount_pct,
         SUM(s.units_sold) AS units_promo
  FROM promotions pr
  JOIN pos_sales s
    ON s.product_id = pr.product_id
   AND s.sale_date BETWEEN pr.start_date AND pr.end_date
  GROUP BY pr.promo_id, pr.product_id, pr.discount_pct
),
baseline AS (
  SELECT pr.promo_id,
         SUM(s.units_sold) / 4.0 AS units_per_week_baseline
  FROM promotions pr
  JOIN pos_sales s
    ON s.product_id = pr.product_id
   AND s.sale_date >= DATEADD(day, -28, pr.start_date)
   AND s.sale_date <  pr.start_date
  GROUP BY pr.promo_id
)
SELECT pu.promo_id, pu.product_id, pu.discount_pct,
       pu.units_promo, ROUND(b.units_per_week_baseline, 1) AS baseline_week,
       ROUND(pu.units_promo / NULLIF(b.units_per_week_baseline, 0), 2) AS uplift_factor
FROM promo_units pu JOIN baseline b USING (promo_id)
ORDER BY uplift_factor DESC;

-- 7. Top 5 products by revenue per store, June 2026
-- Snowflake QUALIFY version:
SELECT store_id, product_id,
       SUM(units_sold * unit_price) AS revenue,
       RANK() OVER (PARTITION BY store_id ORDER BY SUM(units_sold * unit_price) DESC) AS rnk
FROM pos_sales
WHERE sale_date BETWEEN '2026-06-01' AND '2026-06-30'
GROUP BY store_id, product_id
QUALIFY rnk <= 5;
-- Elsewhere: wrap in a subquery/CTE and filter WHERE rnk <= 5.

-- 8. Current vs previous list price (LAG)
SELECT product_id, valid_from, list_price,
       LAG(list_price) OVER (PARTITION BY product_id ORDER BY valid_from) AS prev_price,
       ROUND(100 * (list_price - LAG(list_price) OVER (PARTITION BY product_id ORDER BY valid_from))
             / NULLIF(LAG(list_price) OVER (PARTITION BY product_id ORDER BY valid_from), 0), 1) AS pct_change
FROM price_history
ORDER BY product_id, valid_from;

-- 9. Running monthly revenue per category through 2025
WITH m AS (
  SELECT p.category, DATE_TRUNC('month', s.sale_date) AS month,
         SUM(s.units_sold * s.unit_price) AS revenue
  FROM pos_sales s JOIN products p USING (product_id)
  WHERE YEAR(s.sale_date) = 2025
  GROUP BY p.category, DATE_TRUNC('month', s.sale_date)
)
SELECT category, month, revenue,
       SUM(revenue) OVER (PARTITION BY category ORDER BY month) AS running_total
FROM m ORDER BY category, month;

-- 10. Rolling 12M revenue per category
WITH m AS (
  SELECT p.category, DATE_TRUNC('month', s.sale_date) AS month,
         SUM(s.units_sold * s.unit_price) AS revenue
  FROM pos_sales s JOIN products p USING (product_id)
  GROUP BY p.category, DATE_TRUNC('month', s.sale_date)
)
SELECT category, month, revenue,
       SUM(revenue) OVER (PARTITION BY category ORDER BY month
                          ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS rolling_12m
FROM m ORDER BY category, month;
-- DAX twin: CALCULATE(SUM(...), DATESINPERIOD(DimDate[Date], MAX(DimDate[Date]), -12, MONTH))

-- 11. Store revenue quartiles 2025 + assortment breadth
WITH store_rev AS (
  SELECT store_id, SUM(units_sold * unit_price) AS revenue,
         COUNT(DISTINCT product_id) AS breadth
  FROM pos_sales WHERE YEAR(sale_date) = 2025
  GROUP BY store_id
),
q AS (
  SELECT store_id, revenue, breadth, NTILE(4) OVER (ORDER BY revenue DESC) AS quartile
  FROM store_rev
)
SELECT quartile, COUNT(*) AS stores, ROUND(AVG(revenue)) AS avg_revenue, ROUND(AVG(breadth), 1) AS avg_breadth
FROM q GROUP BY quartile ORDER BY quartile;

-- 12. MoM revenue growth per region
WITH m AS (
  SELECT st.region, DATE_TRUNC('month', s.sale_date) AS month,
         SUM(s.units_sold * s.unit_price) AS revenue
  FROM pos_sales s JOIN stores st USING (store_id)
  GROUP BY st.region, DATE_TRUNC('month', s.sale_date)
)
SELECT region, month, revenue,
       ROUND(100 * (revenue - LAG(revenue) OVER (PARTITION BY region ORDER BY month))
             / NULLIF(LAG(revenue) OVER (PARTITION BY region ORDER BY month), 0), 1) AS mom_growth_pct
FROM m ORDER BY region, month;

-- 13. Best revenue day per product (ROW_NUMBER guarantees exactly one row even on ties)
WITH daily AS (
  SELECT product_id, sale_date, SUM(units_sold * unit_price) AS revenue
  FROM pos_sales GROUP BY product_id, sale_date
)
SELECT product_id, sale_date, revenue
FROM daily
QUALIFY ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY revenue DESC, sale_date) = 1;

-- 14. Dedup pattern
SELECT *
FROM pos_sales
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY sale_date, store_id, product_id, unit_price, promo_flag
  ORDER BY sale_date) = 1;

-- 15. Reconciliation (run both, compare — or join them)
SELECT DATE_TRUNC('month', sale_date) AS month, COUNT(*) AS row_cnt, SUM(units_sold) AS units
FROM pos_sales GROUP BY 1 ORDER BY 1;
-- vs. the same aggregate computed from your summary/mart table; a FULL OUTER JOIN
-- on month with difference columns is the productionized version.

-- 16. Referential integrity probes (expect zero rows)
SELECT DISTINCT s.product_id FROM pos_sales s
LEFT JOIN products p USING (product_id) WHERE p.product_id IS NULL;
SELECT DISTINCT s.store_id FROM pos_sales s
LEFT JOIN stores st USING (store_id) WHERE st.store_id IS NULL;

-- 17. Charm pricing shares
SELECT RIGHT(TO_VARCHAR(unit_price, '999990.00'), 2) AS ending,
       COUNT(*) AS rows_cnt,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM pos_sales GROUP BY 1 ORDER BY rows_cnt DESC LIMIT 10;

-- 18. Beer weekly price vs units (for scatter)
SELECT DATE_TRUNC('week', s.sale_date) AS week,
       AVG(s.unit_price) AS avg_price, SUM(s.units_sold) AS units
FROM pos_sales s JOIN products p USING (product_id)
WHERE p.category = 'Bier'
GROUP BY 1 ORDER BY 1;
