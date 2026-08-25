-- ====================================================================
-- QUERY 1: Rolling 30-Day and 90-Day Retention Rates Post-Orientation
-- Calculates rolling average retention rates over time using window functions.
-- ====================================================================
-- @name: rolling_retention
WITH OrientationCohort AS (
    SELECT 
        strftime('%Y-%m', orientation_date) AS orientation_month,
        COUNT(employee_id) AS total_orientation_completers,
        SUM(CASE 
            WHEN retention_status = 'Exited' 
            AND (julianday(exit_date) - julianday(orientation_date)) <= 30.0 
            THEN 1 ELSE 0 
        END) AS exits_within_30_days,
        SUM(CASE 
            WHEN retention_status = 'Exited' 
            AND (julianday(exit_date) - julianday(orientation_date)) <= 90.0 
            THEN 1 ELSE 0 
        END) AS exits_within_90_days
    FROM Fact_Employee_Events
    WHERE orientation_completed = 1
    GROUP BY orientation_month
),
RetentionRates AS (
    SELECT
        orientation_month,
        total_orientation_completers,
        exits_within_30_days,
        exits_within_90_days,
        ROUND((1.0 - (CAST(exits_within_30_days AS REAL) / total_orientation_completers)) * 100.0, 2) AS retention_rate_30_day,
        ROUND((1.0 - (CAST(exits_within_90_days AS REAL) / total_orientation_completers)) * 100.0, 2) AS retention_rate_90_day
    FROM OrientationCohort
    WHERE orientation_month IS NOT NULL
)
SELECT
    orientation_month,
    total_orientation_completers,
    retention_rate_30_day AS retention_rate_30,
    retention_rate_90_day AS retention_rate_90,
    -- 3-Month Rolling Average Retention Rates using Window Functions
    ROUND(AVG(retention_rate_30_day) OVER (
        ORDER BY orientation_month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_retention_30,
    ROUND(AVG(retention_rate_90_day) OVER (
        ORDER BY orientation_month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_retention_90
FROM RetentionRates
ORDER BY orientation_month;


-- ====================================================================
-- QUERY 2: 12-Month Cohort Retention
-- Tracks retention curves for employee hiring cohorts over a 12-month window.
-- ====================================================================
-- @name: cohort_retention
WITH CohortBase AS (
    SELECT
        strftime('%Y-%m', hire_date) AS cohort_month,
        COUNT(employee_id) AS cohort_size,
        -- Calculate active employees at specific month increments
        -- If active or exited after the given days threshold, count as retained
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 0 THEN 1 ELSE 0 END) AS m0_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 30.4 THEN 1 ELSE 0 END) AS m1_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 60.8 THEN 1 ELSE 0 END) AS m2_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 91.3 THEN 1 ELSE 0 END) AS m3_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 121.7 THEN 1 ELSE 0 END) AS m4_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 152.2 THEN 1 ELSE 0 END) AS m5_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 182.6 THEN 1 ELSE 0 END) AS m6_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 273.9 THEN 1 ELSE 0 END) AS m9_retained,
        SUM(CASE WHEN exit_date IS NULL OR (julianday(exit_date) - julianday(hire_date)) >= 365.25 THEN 1 ELSE 0 END) AS m12_retained
    FROM Fact_Employee_Events
    GROUP BY cohort_month
)
SELECT
    cohort_month,
    cohort_size,
    ROUND((m0_retained * 100.0) / cohort_size, 1) AS m0_pct,
    ROUND((m1_retained * 100.0) / cohort_size, 1) AS m1_pct,
    ROUND((m2_retained * 100.0) / cohort_size, 1) AS m2_pct,
    ROUND((m3_retained * 100.0) / cohort_size, 1) AS m3_pct,
    ROUND((m4_retained * 100.0) / cohort_size, 1) AS m4_pct,
    ROUND((m5_retained * 100.0) / cohort_size, 1) AS m5_pct,
    ROUND((m6_retained * 100.0) / cohort_size, 1) AS m6_pct,
    ROUND((m9_retained * 100.0) / cohort_size, 1) AS m9_pct,
    ROUND((m12_retained * 100.0) / cohort_size, 1) AS m12_pct
FROM CohortBase
WHERE cohort_month IS NOT NULL
ORDER BY cohort_month;


-- ====================================================================
-- QUERY 3: Department Rankings by Training Participation and Retention Delta
-- Ranks departments on how well training improves retention using window ranking.
-- ====================================================================
-- @name: dept_rankings
WITH DeptMetrics AS (
    SELECT 
        d.dept_id,
        d.dept_name,
        d.division,
        COUNT(e.employee_id) AS total_employees,
        -- Participation rates in orientation and navigator school
        SUM(e.orientation_completed) AS orientation_completers,
        SUM(e.navigator_school_completed) AS navigator_school_completers,
        ROUND((SUM(e.orientation_completed) * 100.0) / COUNT(e.employee_id), 2) AS orientation_participation_rate,
        ROUND((SUM(e.navigator_school_completed) * 100.0) / COUNT(e.employee_id), 2) AS navigator_participation_rate,
        
        -- Retention of trained employees (completed orientation OR navigator school)
        SUM(CASE 
            WHEN (e.orientation_completed = 1 OR e.navigator_school_completed = 1) 
            AND e.retention_status = 'Active' 
            THEN 1 ELSE 0 
        END) AS active_trained,
        SUM(CASE 
            WHEN (e.orientation_completed = 1 OR e.navigator_school_completed = 1) 
            THEN 1 ELSE 0 
        END) AS total_trained,
        
        -- Retention of untrained employees (neither completed orientation nor navigator school)
        SUM(CASE 
            WHEN (e.orientation_completed = 0 AND e.navigator_school_completed = 0) 
            AND e.retention_status = 'Active' 
            THEN 1 ELSE 0 
        END) AS active_untrained,
        SUM(CASE 
            WHEN (e.orientation_completed = 0 AND e.navigator_school_completed = 0) 
            THEN 1 ELSE 0 
        END) AS total_untrained
    FROM Dim_Department d
    LEFT JOIN Fact_Employee_Events e ON d.dept_id = e.dept_id
    GROUP BY d.dept_id, d.dept_name, d.division
),
RetentionCalculated AS (
    SELECT
        dept_name,
        division,
        total_employees,
        orientation_participation_rate,
        navigator_participation_rate,
        -- Retention rates
        ROUND((active_trained * 100.0) / NULLIF(total_trained, 0), 2) AS trained_retention_rate,
        ROUND((active_untrained * 100.0) / NULLIF(total_untrained, 0), 2) AS untrained_retention_rate
    FROM DeptMetrics
),
Deltas AS (
    SELECT
        dept_name,
        division,
        total_employees,
        orientation_participation_rate,
        navigator_participation_rate,
        trained_retention_rate,
        untrained_retention_rate,
        -- The delta impact of training
        ROUND(trained_retention_rate - untrained_retention_rate, 2) AS retention_delta
    FROM RetentionCalculated
)
SELECT
    dept_name,
    division,
    total_employees,
    orientation_participation_rate,
    navigator_participation_rate,
    trained_retention_rate,
    untrained_retention_rate,
    retention_delta,
    -- Rank departments using Window Functions
    DENSE_RANK() OVER (ORDER BY retention_delta DESC) AS delta_rank,
    DENSE_RANK() OVER (ORDER BY orientation_participation_rate DESC) AS participation_rank
FROM Deltas
ORDER BY retention_delta DESC;
