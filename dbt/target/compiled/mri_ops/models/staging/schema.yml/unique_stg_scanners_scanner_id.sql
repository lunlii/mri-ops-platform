
    
    

select
    scanner_id as unique_field,
    count(*) as n_records

from "mri_ops"."main"."stg_scanners"
where scanner_id is not null
group by scanner_id
having count(*) > 1


