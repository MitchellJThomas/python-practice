import json
import logging
import urllib.parse as url
from datetime import date, timedelta
from typing import (
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypedDict,
    cast,
    get_args,
    get_type_hints,
)

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

log = logging.getLogger(__name__)

OCIContentDescriptor = TypedDict(
    "OCIContentDescriptor",
    {
        #################
        # Media type values MUST comply with RFC 6838,
        # including the naming requirements in its section
        # 4.2. including OCI types found in mime.types taken from
        # https://github.com/opencontainers/image-spec/blob/master/descriptor.md
        "mediaType": str,
        #################
        # Digest values following the form
        # https://github.com/opencontainers/image-spec/blob/master/descriptor.md#digests
        # digest                ::= algorithm ":" encoded
        # algorithm ::= algorithm-component
        #   (algorithm-separator algorithm-component)*
        # algorithm-component   ::= [a-z0-9]+
        # algorithm-separator   ::= [+._-]
        # encoded               ::= [a-zA-Z0-9=_-]+
        # Registered Algorithms are "sha512" and "sha256"
        "digest": str,
        #################
        # The size property the size, in bytes, of the raw
        # content. This property exists so that a client will have an
        # expected size for the content before processing. If the
        # length of the retrieved content does not match the specified
        # length, the content SHOULD NOT be trusted.  Note: Size
        # should accomodate int64. Python3 int's can indeed do that
        # e.g. int.bit_length(pow(2, 63))
        "size": int,
        #################
        # URLs specifies a list of URIs from which this
        # object MAY be downloaded. Each entry MUST conform to RFC
        # 3986. Entries SHOULD use the http and https schemes, as
        # defined in RFC 7230.
        "urls": Optional[Set[url.ParseResult]],
        #################
        # Annotations contains arbitrary metadata for this descriptor.
        # https://github.com/opencontainers/image-spec/blob/master/annotations.md#rules
        "annotations": Optional[Mapping[str, str]],
    },
)

OCIManifest = TypedDict(
    "OCIManifest",
    {
        #################
        # Schema version specifies the image manifest schema
        # version. For this version of the specification, this MUST be
        # 2 to ensure backward compatibility with older versions of
        # Docker. The value of this field will not change. This field
        # MAY be removed in a future version of the
        # specification. Taken from
        # https://github.com/opencontainers/image-spec/blob/master/manifest.md
        "schemaVersion": int,
        #################
        # Media type reserved for use to maintain
        # compatibility. When used, this field contains the media type
        # of this document, which differs from the descriptor use of
        # mediaType.
        "mediaType": Optional[str],
        #################
        # The configuration object for a container, by digest.
        "config": OCIContentDescriptor,
        #################
        # The layers of the image. A final filesystem layout MUST
        # match the result of applying the layers to an empty
        # directory. The ownership, mode, and other attributes of the
        # initial empty directory are unspecified.
        "layers": Sequence[OCIContentDescriptor],
        #################
        # Arbitrary metadata for the image manifest.
        "annotations": Optional[Mapping[str, str]],
        #################
    },
)


def _required_keys(type_hint):
    """Return those keys which are required for a particular typing hint"""
    return [
        k
        for (k, v) in get_type_hints(type_hint).items()
        if type(None) not in get_args(v)
    ]


def build_manifest(
    manifest: Mapping[str, str]
) -> Tuple[Optional[OCIManifest], Optional[Exception]]:
    """Verify and build a manifest typed dictionary from a Mapping e.g. something parsed by json.loads
    This takes the Python typing hints and applies them (partially) at runtime"""

    # Verify top level manifest has the required keys
    for k in _required_keys(OCIManifest):
        if k not in manifest:
            return (None, Exception(f"Manifest {manifest} must contain key {k}"))

    # Verify config in manifest has required keys
    required_descriptor_keys = _required_keys(OCIContentDescriptor)
    config = manifest["config"]
    for k in required_descriptor_keys:
        if k not in config:
            return (None, Exception(f"Manifest {manifest} config must contain key {k}"))

    # Verify layers in manifest have the required keys
    for k in required_descriptor_keys:
        for layer in manifest["layers"]:
            if k not in layer:
                return (
                    None,
                    Exception(
                        f"Manifest {manifest} layer {layer} must contain key {k}"
                    ),
                )

    # Verify values in the manifest
    if manifest["schemaVersion"] != 2:
        return (None, Exception(f"Manifest {manifest} schemaVersion must be 2"))

    return (cast(OCIManifest, manifest), None)


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


def create_partition_table_statements(num_weeks: int) -> Sequence[str]:
    today = date.today()
    return [
        create_partition_table_statement(
            "manifest_layers", (today + timedelta(weeks=x))
        )
        for x in range(num_weeks)
    ]


def create_json(manifest: OCIManifest, layer: OCIContentDescriptor) -> Tuple[str, str]:
    manifest_config = manifest["config"]
    annotations_json = json.dumps(
        {
            "layer": layer.get("annotations", {}),
            "manifest_config": manifest_config.get("annotations", {}),
            "manifest": manifest.get("annotations", {}),
        }
    )
    urls_json = json.dumps(
        {
            "layer": layer.get("urls", []),
            "manifest_config_urls": manifest_config.get("urls", []),
        }
    )
    return (annotations_json, urls_json)


async def insert_manifest(
    conn: asyncpg.connection.Connection, manifest: OCIManifest
) -> Tuple[Optional[str], Optional[Exception]]:
    try:
        layer_order = 0
        manifest_config = manifest["config"]
        for layer in manifest["layers"]:
            annotations_json, urls_json = create_json(manifest, layer)

            digest = layer["digest"]
            ts = await conn.fetchval(
                """INSERT INTO manifest_layers(
            annotations,
            digest,
            media_type,
            layer_order,
            layer_size,
            urls,
            manifest_config_digest,
            manifest_config_media_type,
            manifest_config_size,
            manifest_media_type,
            manifest_schema_version) VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING ts
            """,
                annotations_json,
                digest,
                layer["mediaType"],
                layer_order,
                layer["size"],
                urls_json,
                manifest_config["digest"],
                manifest_config["mediaType"],
                manifest_config["size"],
                manifest.get("mediaType", ""),
                manifest["schemaVersion"],
            )

            log.info(f"Inserted manifest layer digest {digest} at timestamp {ts}")
            layer_order += 1
        return (str(ts), None)
    except Exception as e:
        return (None, e)


async def conn_pool(app):
    app.logger.info("Initializing Postgres connection pool")
    app["conn_pool"] = await asyncpg.create_pool(command_timeout=60)
    yield
    app.logger.info("Closing Postgres connection pool")
    await app["conn_pool"].close()
