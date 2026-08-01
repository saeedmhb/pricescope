USE SCHEMA PRICESCOPE.RAW;

CREATE OR REPLACE TABLE RAW_PRODUCTS (
  product_id          VARCHAR,
  ean                 VARCHAR,
  product_name        VARCHAR,
  category            VARCHAR,
  brand               VARCHAR,
  unit_size           VARCHAR,
  unit_cost           VARCHAR,
  initial_list_price  VARCHAR,
  _SOURCE_FILE        VARCHAR,
  _LOADED_AT          TIMESTAMP_LTZ
);

CREATE OR REPLACE TABLE RAW_STORES (
  store_id      VARCHAR,
  store_name    VARCHAR,
  city          VARCHAR,
  region        VARCHAR,
  store_format  VARCHAR,
  opened_date   VARCHAR,
  _SOURCE_FILE  VARCHAR,
  _LOADED_AT    TIMESTAMP_LTZ
);

CREATE OR REPLACE TABLE RAW_PRICE_HISTORY (
  product_id    VARCHAR,
  list_price    VARCHAR,
  valid_from    VARCHAR,
  valid_to      VARCHAR,
  _SOURCE_FILE  VARCHAR,
  _LOADED_AT    TIMESTAMP_LTZ
);

CREATE OR REPLACE TABLE RAW_PROMOTIONS (
  promo_id      VARCHAR,
  product_id    VARCHAR,
  start_date    VARCHAR,
  end_date      VARCHAR,
  discount_pct  VARCHAR,
  _SOURCE_FILE  VARCHAR,
  _LOADED_AT    TIMESTAMP_LTZ
);

CREATE OR REPLACE TABLE RAW_POS_SALES (
  sale_date     VARCHAR,
  store_id      VARCHAR,
  product_id    VARCHAR,
  units_sold    VARCHAR,
  unit_price    VARCHAR,
  promo_flag    VARCHAR,
  _SOURCE_FILE  VARCHAR,
  _LOADED_AT    TIMESTAMP_LTZ
);

CREATE OR REPLACE TABLE RAW_COMPETITOR_PRICES (
  RAW_JSON      VARIANT,
  _SOURCE_FILE  VARCHAR,
  _LOADED_AT    TIMESTAMP_LTZ
);

CREATE OR REPLACE TABLE RAW_WEATHER (
  RAW_JSON      VARIANT,
  _SOURCE_FILE  VARCHAR,
  _LOADED_AT    TIMESTAMP_LTZ
);