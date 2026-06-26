with source as (
    select * from read_csv_auto('{{ env_var("DBT_DATA_PATH", "../data/synthetic") }}/scanners.csv')
),

renamed as (
    select
        scanner_id,
        site,
        field_strength,
        status,
        open_bore::boolean    as open_bore,
        delay_bias_min::float as delay_bias_min
    from source
)

select * from renamed
