with adherence as (
    select * from {{ ref('int_schedule_adherence') }}
),

procedure_stats as (
    select
        procedure_code,
        procedure_name,
        complexity,
        is_contrast,
        count(*)                                                      as total_exams,
        round(avg(template_duration_min), 1)                          as template_duration_min,
        round(avg(actual_duration_min), 1)                            as avg_actual_duration_min,
        round(stddev(actual_duration_min), 1)                         as stddev_duration_min,
        round(avg(actual_duration_min) - avg(template_duration_min), 1) as avg_duration_variance_min,
        round(avg(case when adherent then 1.0 else 0.0 end) * 100, 1) as adherence_rate_pct,
        round(avg(start_delay_min), 1)                                as avg_start_delay_min,
        round(avg(end_delta_min), 1)                                  as avg_end_delta_min,
        -- p90 actual duration
        round(percentile_cont(0.90) within group (order by actual_duration_min), 1) as p90_duration_min,
        -- p90 end delta (how late do the worst exams run?)
        round(percentile_cont(0.90) within group (order by end_delta_min), 1)       as p90_end_delta_min,
        count(case when duration_vs_template = 'over' then 1 end)     as exams_over_template,
        count(case when duration_vs_template = 'under' then 1 end)    as exams_under_template
    from adherence
    group by procedure_code, procedure_name, complexity, is_contrast
)

select * from procedure_stats
order by avg_duration_variance_min desc
