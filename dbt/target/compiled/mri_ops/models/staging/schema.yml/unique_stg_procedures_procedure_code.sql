
    
    

select
    procedure_code as unique_field,
    count(*) as n_records

from "mri_ops"."main"."stg_procedures"
where procedure_code is not null
group by procedure_code
having count(*) > 1


