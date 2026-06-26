with source as (
    select * from read_csv_auto('{{ env_var("DBT_DATA_PATH", "../data/synthetic") }}/actual_exam_logs.csv')
),

renamed as (
    select
        log_id,
        appointment_id,
        actual_start::timestamp      as actual_start,
        actual_end::timestamp        as actual_end,
        actual_duration_min::float   as actual_duration_min,
        start_delay_min::float       as start_delay_min,
        end_delta_min::float         as end_delta_min,
        adherent::boolean            as adherent,
        delay_reason,
        technologist_id
    from source
)

select * from renamed
