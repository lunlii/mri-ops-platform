
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select log_id
from "mri_ops"."main"."stg_exam_logs"
where log_id is null



  
  
      
    ) dbt_internal_test