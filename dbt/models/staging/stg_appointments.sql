with source as (
    select * from read_csv_auto('{{ env_var("DBT_DATA_PATH", "../data/synthetic") }}/appointments.csv')
),

renamed as (
    select
        appointment_id,
        patient_id,
        procedure_code,
        scanner_id,
        site,
        scheduled_start::timestamp     as scheduled_start,
        scheduled_end::timestamp       as scheduled_end,
        template_duration_min::integer as template_duration_min,
        day_of_week,
        hour_of_day::integer           as hour_of_day,
        is_contrast::boolean           as is_contrast,
        complexity
    from source
)

select * from renamed
