with exam_durations as (
    select * from {{ ref('int_exam_durations') }}
),

scanners as (
    select * from {{ ref('stg_scanners') }}
),

final as (
    select
        e.appointment_id,
        e.procedure_code,
        e.procedure_name,
        e.scanner_id,
        s.site,
        s.field_strength,
        e.exam_date,
        e.day_of_week,
        e.hour_of_day,
        e.complexity,
        e.is_contrast,
        e.template_duration_min,
        e.actual_duration_min,
        e.start_delay_min,
        e.end_delta_min,
        e.adherent,
        e.delay_reason,
        e.duration_variance_min,
        e.duration_vs_template,

        -- Risk buckets for dashboard
        case
            when e.start_delay_min >= 15 then 'high'
            when e.start_delay_min >= 5  then 'medium'
            else 'low'
        end as start_delay_risk,

        case
            when abs(e.end_delta_min) <= 5  then 'on_time'
            when abs(e.end_delta_min) <= 10 then 'near_miss'
            when e.end_delta_min > 10       then 'late'
            else 'early'
        end as adherence_category

    from exam_durations e
    inner join scanners s on e.scanner_id = s.scanner_id
)

select * from final
