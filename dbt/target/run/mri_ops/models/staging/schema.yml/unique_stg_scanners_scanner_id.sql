
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    scanner_id as unique_field,
    count(*) as n_records

from "mri_ops"."main"."stg_scanners"
where scanner_id is not null
group by scanner_id
having count(*) > 1



  
  
      
    ) dbt_internal_test