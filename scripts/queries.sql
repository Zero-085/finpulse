-- FinPulse SQL Analysis
-- Personal finance transaction analysis


-- 1. Overall spending summary

SELECT
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_spend,
    ROUND(AVG(amount), 2) AS average_transaction,
    ROUND(MIN(amount), 2) AS minimum_transaction,
    ROUND(MAX(amount), 2) AS maximum_transaction
FROM transactions;

-- 2. Category spending contribution

SELECT
    category,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_spend,
    ROUND(AVG(amount), 2) AS average_transaction,
    ROUND(
        100.0 * SUM(amount) / SUM(SUM(amount)) OVER (),
        2
    ) AS spend_percentage
FROM transactions
GROUP BY category
ORDER BY total_spend DESC;

-- 3. Month-over-month spending growth

WITH monthly_spending AS (
    SELECT
        year,
        month,
        month_number,
        ROUND(SUM(amount), 2) AS total_spend
    FROM transactions
    GROUP BY year, month, month_number
),

spending_comparison AS (
    SELECT
        year,
        month,
        month_number,
        total_spend,
        LAG(total_spend) OVER (
            ORDER BY year, month_number
        ) AS previous_month_spend
    FROM monthly_spending
)

SELECT
    year,
    month,
    total_spend,
    previous_month_spend,
    ROUND(
        100.0 * (total_spend - previous_month_spend)
        / previous_month_spend,
        2
    ) AS mom_growth_percentage
FROM spending_comparison
ORDER BY year, month_number;

-- 4. Anomaly impact analysis

SELECT
    is_anomaly,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_spend,
    ROUND(AVG(amount), 2) AS average_transaction,
    ROUND(
        100.0 * SUM(amount) / SUM(SUM(amount)) OVER (),
        2
    ) AS spend_percentage
FROM transactions
GROUP BY is_anomaly
ORDER BY is_anomaly DESC;

-- 5. Weekend vs weekday spending behaviour

SELECT
    CASE
        WHEN is_weekend = 1 THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_spend,
    ROUND(AVG(amount), 2) AS average_transaction,
    ROUND(
        100.0 * SUM(amount) / SUM(SUM(amount)) OVER (),
        2
    ) AS spend_percentage
FROM transactions
GROUP BY is_weekend
ORDER BY total_spend DESC;

-- 6. Top merchants by spending

SELECT
    merchant,
    category,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_spend,
    ROUND(AVG(amount), 2) AS average_transaction,
    DENSE_RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS spend_rank
FROM transactions
GROUP BY merchant, category
ORDER BY spend_rank
LIMIT 10;

-- 7. Spending tier distribution and impact

SELECT
    spending_tier,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_spend,
    ROUND(AVG(amount), 2) AS average_transaction,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS transaction_percentage,
    ROUND(
        100.0 * SUM(amount) / SUM(SUM(amount)) OVER (),
        2
    ) AS spend_percentage
FROM transactions
GROUP BY spending_tier
ORDER BY total_spend DESC;

-- 8. Monthly category spending rank

WITH category_monthly_spend AS (
    SELECT
        year,
        month,
        month_number,
        category,
        ROUND(SUM(amount), 2) AS total_spend
    FROM transactions
    GROUP BY
        year,
        month,
        month_number,
        category
)

SELECT
    year,
    month,
    category,
    total_spend,
    DENSE_RANK() OVER (
        PARTITION BY year, month_number
        ORDER BY total_spend DESC
    ) AS category_rank
FROM category_monthly_spend
ORDER BY
    year,
    month_number,
    category_rank;