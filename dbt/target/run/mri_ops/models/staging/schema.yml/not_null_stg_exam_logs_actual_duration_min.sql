
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select actual_duration_min
from "mri_ops"."main"."stg_exam_logs"
where actual_duration_min is null



  
  
      
    ) dbt_internal_test