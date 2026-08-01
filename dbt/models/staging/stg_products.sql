-- Product master data: type casting and renaming only.
select
    product_id::varchar                 as product_id,
    ean::varchar                        as ean,
    product_name::varchar               as product_name,
    category::varchar                   as category,
    brand::varchar                      as brand,
    unit_size::varchar                  as unit_size,
    unit_cost::number(10,2)             as unit_cost_eur,
    initial_list_price::number(10,2)    as initial_list_price_eur,
    _source_file                        as source_file,
    _loaded_at                          as loaded_at
from {{ source('raw', 'RAW_PRODUCTS') }}