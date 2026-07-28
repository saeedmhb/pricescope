# Day 1 SQL drills — PriceScope dataset

Work through these in order. Solutions in `day1_solutions.sql` — attempt first, peek after.
Syntax is standard SQL / Snowflake-compatible. If you drill locally today, load
`master/*.csv` + one or two `sales/pos_sales_*.csv` into any database (Postgres, SQL Server,
DuckDB — `duckdb` + `read_csv_auto()` is the fastest zero-setup option).

Tables: `pos_sales` (sale_date, store_id, product_id, units_sold, unit_price, promo_flag),
`products`, `stores`, `price_history`, `promotions`.

## Warm-up (20 min)
1. Total revenue (units × price) per category, ordered descending.
2. Number of distinct products sold per store in March 2025. Which store has the narrowest active assortment?
3. Average selling price per category, promo vs. non-promo rows side by side (one row per category, two columns — hint: conditional aggregation).

## Joins & aggregation (30 min)
4. Revenue per region (Berlin vs. Brandenburg) per month. Add a % of total column.
5. Products that were sold at least once in 2024 but never in 2026 (delisting candidates). Hint: anti-join.
6. For each promotion in `promotions`, the actual units sold during the promo window vs. the 4 weeks before (promo uplift per promo). This is a real pricing-analyst query — take your time.

## Window functions (60 min — the core block)
7. Top 5 products by revenue **per store** for June 2026. (RANK/DENSE_RANK + QUALIFY in Snowflake, or a subquery elsewhere.)
8. For each product: current list price and previous list price from `price_history`, plus the % change. (LAG over valid_from.)
9. Running monthly revenue total per category through 2025 (SUM OVER with ORDER BY).
10. Rolling 12-month revenue per category for each month (ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) — the SQL twin of your DAX Rolling 12M measure. Say out loud how the two relate.
11. Divide stores into revenue quartiles for 2025 (NTILE(4)). Then: average assortment breadth per quartile.
12. Month-over-month revenue growth % per region (LAG on a monthly aggregate CTE).
13. For each product, the date of its single best revenue day (ROW_NUMBER = 1 pattern). Note why ROW_NUMBER, not RANK, guarantees one row.

## Data quality / dedup patterns (30 min)
14. Suppose `pos_sales` accidentally contained exact duplicate rows. Write the dedup query (ROW_NUMBER over all business keys, keep rn = 1). You'll reuse this pattern in dbt staging.
15. Reconciliation check: row count + SUM(units_sold) per month in the raw table vs. an aggregated summary you create — the two-query "Abstimmung" pattern from your CV, written fresh.
16. Referential integrity probe: any product_id in `pos_sales` missing from `products`? Any store_id missing from `stores`? (Should be zero — write the query that proves it.)

## Stretch (if time remains)
17. Price-ending analysis: what share of shelf prices end in .99 vs .49 vs other? (Pricing teams love charm-pricing questions.)
18. For beer only: weekly average price vs. weekly units, output ready for a scatter plot — your first look at the elasticity you'll estimate properly on Day 5.

## Self-check before closing the day
- Can you explain QUALIFY vs. HAVING vs. WHERE in one sentence each?
- Can you write LAG and a rolling window without looking anything up?
- Can you explain why ROW_NUMBER/RANK/DENSE_RANK differ, with the tie case?
