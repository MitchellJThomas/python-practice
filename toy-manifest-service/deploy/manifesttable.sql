-- Deploy flipr:manifesttable to pg

BEGIN;

CREATE TABLE manifest_layers (
  annotations              jsonb,
  digest                   text not null,
  media_type               text not null,
  layer_order              smallint not null,
  layer_size               bigint not null,
  ts                       timestamptz DEFAULT NOW(),
  urls                     jsonb,

  manifest_config_digest     text not null,
  manifest_config_media_type text not null,
  manifest_config_size       bigint not null,
  manifest_media_type        text,
  manifest_schema_version    smallint not null
)
PARTITION BY RANGE (ts);

COMMIT;
