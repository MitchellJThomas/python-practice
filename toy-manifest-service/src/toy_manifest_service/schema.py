from datetime import date, timedelta
from functools import partial

import asyncpg

# Single table Postgres schema (version 13)
# De-normalized per layer, Annotations JSONB
# where urls_json = {
#     "layer": ["url1", "url2"]
#     "manifest_config_urls": ["url1", "url2"]
#     }
# where annotations_json = {
#     "layer": {}
#     "manfiest_config": {},
#     "manifest": {},
#    }
# Partitioning scheme notes
# https://minervadb.com/index.php/postgresql-dynamic-partitioning/
# https://www.postgresql.org/docs/13/ddl-partitioning.html
# Range partitioning by timestamp


def create_manifest_layers_statement(num_weeks: int):
    """Create the de-normalized OCI manifest+layer table(s) and indicies
    using JSON for annotations and urls
    See https://www.postgresql.org/docs/13/ddl-partitioning.html for partition details
    """
    partition_statements = "".join(
        [t for t in create_partition_table_statements(num_weeks)]
    )
    main_statement = """
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
  manifest_schema_version    smallint not null,

)
PARTITION BY RANGE (ts);
COMMIT;
    """
    index_statements = """
CREATE INDEX manifest_config_digest_idx on manifest_layers (manifest_config_digest);
CREATE INDEX digest_idx on manifest_layers (digest);
    """
    return main_statement + partition_statements + index_statements


def create_partition_table_statement(table_name, start_date):
    """Create year week partition table statements for a given table name and start date"""
    iso_cal = start_date.isocalendar()
    year = iso_cal[0]
    week = iso_cal[1]
    end_date = start_date + timedelta(weeks=1)
    return f"""
CREATE TABLE {table_name}_{week}_{year} PARTITION OF {table_name}
    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
CREATE INDEX {table_name}_{week}_{year}_manifest_config_digest_idx on {table_name}_{week}_{year} (manifest_config_digest);
CREATE INDEX {table_name}_{week}_{year}_digest_idx on {table_name}_{week}_{year} (digest);
    """


def create_partition_table_statements(num_weeks: int):
    today = date.today()
    manifest_layer_tables = partial(create_partition_table_statement, "manifest_layers")
    return map(
        manifest_layer_tables, [(today + timedelta(weeks=x)) for x in range(num_weeks)],
    )


async def conn_pool(app):
    app.logger.info("Initializing Postgres connection pool")
    app["conn_pool"] = await asyncpg.create_pool(command_timeout=60)
    yield
    app.logger.info("Closing Postgres connection pool")
    await app["conn_pool"].close()
