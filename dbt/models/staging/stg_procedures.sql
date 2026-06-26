with source as (
    select * from read_csv_auto('{{ env_var("DBT_DATA_PATH", "../data/synthetic") }}/procedures.csv')
),

renamed as (
    select
        procedure_id::integer          as procedure_id,
        procedure_code,
        procedure_name,
        template_duration_min::integer as template_duration_min,
        contrast_required::boolean     as contrast_required,
        complexity,
        duration_std_pct::float        as duration_std_pct
    from source
)

select * from renamed
