-- =============================================================================
-- analytics.sql  —  Analytical queries run against the DuckDB warehouse.
--
-- These demonstrate the SQL skills on the resume (CTEs, window functions,
-- aggregation, cohort analysis) and feed the dashboard's summary panels.
-- Table: students  (the cleaned, feature-engineered extract)
-- =============================================================================

-- :name overall_kpis
-- Headline KPIs for the top of the dashboard.
SELECT
    COUNT(*)                                   AS total_students,
    ROUND(AVG(not_retained) * 100, 1)          AS not_retained_pct,
    ROUND(AVG(current_gpa), 2)                 AS avg_gpa,
    ROUND(AVG(assignment_submit_rate) * 100, 1) AS avg_submit_pct
FROM students;

-- :name risk_by_major
-- Which programs carry the most retention risk? (cohort comparison)
SELECT
    major,
    COUNT(*)                              AS students,
    ROUND(AVG(not_retained) * 100, 1)     AS not_retained_pct,
    ROUND(AVG(current_gpa), 2)            AS avg_gpa
FROM students
GROUP BY major
HAVING COUNT(*) >= 50
ORDER BY not_retained_pct DESC;

-- :name engagement_decile_retention
-- Retention rate across engagement deciles — shows the engagement→outcome
-- relationship using a window function (NTILE).
WITH ranked AS (
    SELECT
        not_retained,
        NTILE(10) OVER (ORDER BY lms_logins_per_week) AS engagement_decile
    FROM students
)
SELECT
    engagement_decile,
    COUNT(*)                           AS students,
    ROUND(AVG(not_retained) * 100, 1)  AS not_retained_pct
FROM ranked
GROUP BY engagement_decile
ORDER BY engagement_decile;

-- :name first_gen_gap
-- Equity lens: retention gap for first-generation students.
SELECT
    CASE first_gen_flag WHEN 1 THEN 'First-gen' ELSE 'Continuing-gen' END AS cohort,
    COUNT(*)                           AS students,
    ROUND(AVG(not_retained) * 100, 1)  AS not_retained_pct,
    ROUND(AVG(current_gpa), 2)         AS avg_gpa
FROM students
GROUP BY first_gen_flag
ORDER BY not_retained_pct DESC;

-- :name term_trend
-- Trend of the risk outcome across terms.
SELECT
    term,
    COUNT(*)                           AS students,
    ROUND(AVG(not_retained) * 100, 1)  AS not_retained_pct
FROM students
GROUP BY term
ORDER BY term;
