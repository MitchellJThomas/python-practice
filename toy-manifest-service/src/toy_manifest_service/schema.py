from datetime import date, timedelta
from functools import partial

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


def create_manifest_layers_statement():
    return """
    CREATE TABLE manifest_layers (
      creation_date            date not null,
      manifest_config_digest,
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


def create_partition_table_statement(table_name, start_date):
    """Create year week partition table statements for a given table name and start date"""
    iso_cal = start_date.isocalendar()
    year = iso_cal[0]
    week = iso_cal[1]
    end_date = start_date + timedelta(weeks=1)
    return f"CREATE TABLE {table_name}_{week}_{year} PARTITION OF {table_name} FOR VALUES FROM ('{start_date}') TO ('{end_date}');"


def create_partition_table_statements():
    today = date.today()
    manifest_layer_tables = partial(create_partition_table_statement, "manifest_layers")
    return map(
        manifest_layer_tables, [(today + timedelta(weeks=x)) for x in range(52)],
    )


# Partitioning scheme
# https://minervadb.com/index.php/postgresql-dynamic-partitioning/
# https://www.postgresql.org/docs/13/ddl-partitioning.html
# Range partitioning by timestamp
