
    
    

select
    log_id as unique_field,
    count(*) as n_records

from "mri_ops"."main"."stg_exam_logs"
where log_id is not null
group by log_id
having count(*) > 1


