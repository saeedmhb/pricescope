-- List price validity periods per product.
-- valid_to = 9999-12-31 marks the currently active price.
select
    product_id::varchar     as product_id,
    list_price::number(10,2) as list_price_eur,
    valid_from::date        as valid_from,
    valid_to::date          as valid_to,
    valid_to = '9999-12-31'::date as is_current,
    _source_file            as source_file,
    _loaded_at              as loaded_at
from {{ source('raw', 'RAW_PRICE_HISTORY') }}