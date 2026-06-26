with adherence as (
    select * from {{ ref('int_schedule_adherence') }}
),

daily_stats as (
    select
        exam_date,
        scanner_id,
        site,
        field_strength,
        count(*)                                          as total_exams,
        sum(case when adherent then 1 else 0 end)         as adherent_exams,
        round(avg(case when adherent then 1.0 else 0.0 end) * 100, 1) as adherence_rate_pct,
        round(avg(actual_duration_min), 1)                as avg_actual_duration_min,
        round(avg(template_duration_min), 1)              as avg_template_duration_min,
        round(avg(start_delay_min), 1)                    as avg_start_delay_min,
        round(avg(end_delta_min), 1)                      as avg_end_delta_min,
        round(stddev(actual_duration_min), 1)             as stddev_duration_min,
        round(max(start_delay_min), 1)                    as max_start_delay_min,
        round(max(end_delta_min), 1)                      as max_end_delta_min,
        count(case when delay_reason = 'equipment_issue' then 1 end) as equipment_issues,
        count(case when delay_reason = 'patient_late' then 1 end)    as patient_late_count,
        count(case when start_delay_risk = 'high' then 1 end)        as high_delay_risk_count
    from adherence
    group by exam_date, scanner_id, site, field_strength
)

select * from daily_stats
order by exam_date desc, scanner_id
