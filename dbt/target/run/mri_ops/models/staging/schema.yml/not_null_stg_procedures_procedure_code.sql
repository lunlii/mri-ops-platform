
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select procedure_code
from "mri_ops"."main"."stg_procedures"
where procedure_code is null



  
  
      
    ) dbt_internal_test