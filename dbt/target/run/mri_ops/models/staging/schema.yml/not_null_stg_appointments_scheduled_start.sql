
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select scheduled_start
from "mri_ops"."main"."stg_appointments"
where scheduled_start is null



  
  
      
    ) dbt_internal_test