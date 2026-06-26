-- Feature table for ML model training and inference
-- One row per exam with all features needed for duration prediction
-- and schedule adherence classification

with adherence as (
    select * from {{ ref('int_schedule_adherence') }}
),

features as (
    select
        -- Keys
        appointment_id,
        exam_date,

        -- Target variables
        actual_duration_min,
        adherent,

        -- Procedure features
        procedure_code,
        complexity,
        is_contrast,
        template_duration_min,

        -- Time features
        day_of_week,
        hour_of_day,
        case day_of_week
            when 'Monday'    then 1
            when 'Tuesday'   then 2
            when 'Wednesday' then 3
            when 'Thursday'  then 4
            when 'Friday'    then 5
        end as day_of_week_num,
        case
            when hour_of_day between 7  and 9  then 'early_am'
            when hour_of_day between 10 and 12 then 'mid_am'
            when hour_of_day between 13 and 15 then 'early_pm'
            when hour_of_day between 16 and 19 then 'late_pm'
        end as time_bucket,

        -- Scanner features
        scanner_id,
        site,
        field_strength,

        -- Delay context
        start_delay_min,
        delay_reason,
        start_delay_risk

    from adherence
)

select * from features
