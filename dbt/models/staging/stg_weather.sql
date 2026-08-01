-- Daily Berlin weather from Open-Meteo.
-- Source JSON stores parallel arrays; flatten by index to get one row per day.
select
    w.raw_json:daily:time[f.index]::date                        as weather_date,
    w.raw_json:daily:temperature_2m_max[f.index]::number(5,1)   as temp_max_c,
    w.raw_json:daily:temperature_2m_min[f.index]::number(5,1)   as temp_min_c,
    w.raw_json:daily:precipitation_sum[f.index]::number(5,1)    as precipitation_mm,
    w._source_file                                              as source_file,
    w._loaded_at                                                as loaded_at
from {{ source('raw', 'RAW_WEATHER') }} w,
     lateral flatten(input => w.raw_json:daily:time) f