-- Store master data: type casting and renaming only.
select
    store_id::varchar       as store_id,
    store_name::varchar     as store_name,
    city::varchar           as city,
    region::varchar         as region,
    store_format::varchar   as store_format,
    opened_date::date       as opened_date,
    _source_file            as source_file,
    _loaded_at              as loaded_at
from {{ source('raw', 'RAW_STORES') }}