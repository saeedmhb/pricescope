-- Daily POS sales, one row per store/product/day.
-- unit_price is already net of any promotional discount.
select
    sale_date::date             as sale_date,
    store_id::varchar           as store_id,
    product_id::varchar         as product_id,
    units_sold::number(10,0)    as units_sold,
    unit_price::number(10,2)    as unit_price_eur,
    promo_flag::number(1,0) = 1 as is_promo,
    units_sold::number(10,0) * unit_price::number(10,2) as revenue_eur,
    _source_file                as source_file,
    _loaded_at                  as loaded_at
from {{ source('raw', 'RAW_POS_SALES') }}