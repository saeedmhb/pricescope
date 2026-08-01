-- Competitor price observations, flattened from nested JSON.
-- Note: joins to products on EAN, not product_id (~60% coverage).
select
    f.value:competitor::varchar     as competitor_name,
    f.value:ean::varchar            as ean,
    f.value:price::number(10,2)     as competitor_price_eur,
    f.value:observed_at::date       as observed_at,
    c.raw_json:source::varchar      as feed_source,
    c._source_file                  as source_file,
    c._loaded_at                    as loaded_at
from {{ source('raw', 'RAW_COMPETITOR_PRICES') }} c,
     lateral flatten(input => c.raw_json:records) f