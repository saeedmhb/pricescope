-- Promotion periods with discount percentage per product.
select
    promo_id::varchar           as promo_id,
    product_id::varchar         as product_id,
    start_date::date            as promo_start_date,
    end_date::date              as promo_end_date,
    discount_pct::number(5,2)   as discount_pct,
    datediff('day', start_date::date, end_date::date) + 1 as promo_duration_days,
    _source_file                as source_file,
    _loaded_at                  as loaded_at
from {{ source('raw', 'RAW_PROMOTIONS') }}