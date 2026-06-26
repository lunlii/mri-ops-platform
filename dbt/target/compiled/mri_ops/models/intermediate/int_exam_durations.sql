with appointments as (
    select * from "mri_ops"."main"."stg_appointments"
),

exam_logs as (
    select * from "mri_ops"."main"."stg_exam_logs"
),

procedures as (
    select * from "mri_ops"."main"."stg_procedures"
),

joined as (
    select
        a.appointment_id,
        a.patient_id,
        a.procedure_code,
        a.scanner_id,
        a.site,
        a.scheduled_start,
        a.scheduled_end,
        a.template_duration_min,
        a.day_of_week,
        a.hour_of_day,
        a.is_contrast,
        a.complexity,

        l.actual_start,
        l.actual_end,
        l.actual_duration_min,
        l.start_delay_min,
        l.end_delta_min,
        l.adherent,
        l.delay_reason,
        l.technologist_id,

        -- Derived fields
        p.procedure_name,
        l.actual_duration_min - a.template_duration_min as duration_variance_min,
        case
            when l.actual_duration_min > a.template_duration_min then 'over'
            when l.actual_duration_min < a.template_duration_min then 'under'
            else 'on_template'
        end as duration_vs_template,

        date_trunc('day', a.scheduled_start) as exam_date,
        date_part('week', a.scheduled_start) as exam_week,
        date_part('month', a.scheduled_start) as exam_month,
        date_part('year', a.scheduled_start) as exam_year

    from appointments a
    inner join exam_logs l on a.appointment_id = l.appointment_id
    inner join procedures p on a.procedure_code = p.procedure_code
)

select * from joined