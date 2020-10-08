from datetime import date, timedelta
from functools import partial

import asyncpg

# Single table Postgres schema (version 13)
# De-normalized per layer, Annotations JSONB
# where urls_json = {
#     "urls": ["url1", "url2"]
#     }
# where annotations_json = {
#     "manifest": {},
#     "manfiest_config": {},
#     "layer": {}
#    }
# Partitioning scheme notes
# https://minervadb.com/index.php/postgresql-dynamic-partitioning/
# https://www.postgresql.org/docs/13/ddl-partitioning.html
# Range partitioning by timestamp


def create_manifest_layers_statement():
    """Create the de-normalized OCI manifest+layer table(s) and indicies
    using JSON for annotations and urls
    See https://www.postgresql.org/docs/13/ddl-partitioning.html for partition details
    """
    num_weeks = 12
    partition_statements = "".join(
        [t for t in create_partition_table_statements(num_weeks)]
    )
    main_statement = """
    CREATE TABLE manifest_layers (
      creation_date            date not null,
      manifest_config_digest,
      order,
      digest,
      media_type,
      size,
      urls_json,
      annotations_json,
      manifest_schema_ersion,
      manifest_media_type,
      manifest_config_media_type,
      manifest_config_size,
      manifest_config_urls_json
    ) PARTITION BY RANGE (creation_date);
    """
    index_statements = """
    CREATE INDEX on creation_date;
    CREATE INDEX on manifest_config_digest;
    CREATE INDEX on digest;
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
       FOR VALUES FROM ('{start_date}') TO ('{end_date}')
       PARTITION BY RANGE (manifest_config_digest);
    """


def create_partition_table_statements(num_weeks):
    today = date.today()
    manifest_layer_tables = partial(create_partition_table_statement, "manifest_layers")
    return map(
        manifest_layer_tables, [(today + timedelta(weeks=x)) for x in range(num_weeks)],
    )


# print(create_manifest_layers_statement())
async def conn_pool(app):
    app.logger.info("Initializing Postgres connection pool")
    app['conn_pool'] = await asyncpg.create_pool(command_timeout=60)
    yield
    app.logger.info("Closing Postgres connection pool")
    await app['conn_pool'].close()
