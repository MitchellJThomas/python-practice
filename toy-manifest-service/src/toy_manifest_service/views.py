import hashlib
import logging
import os
import typing
import urllib.parse as url
from typing import Mapping, Optional, Sequence, Set, Tuple, TypedDict

import aiofiles
from aiohttp import web

log = logging.getLogger(__name__)

routes = web.RouteTableDef()

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


def required_keys(type_hint):
    """Return those keys which are required for a particular typing hint"""
    return [
        k
        for (k, v) in typing.get_type_hints(type_hint).items()
        if type(None) not in typing.get_args(v)
    ]


def build_manifest(
    manifest: Mapping[str, str]
) -> Tuple[Optional[OCIManifest], Optional[Exception]]:
    """Verify and build a manifest typed dictionary from a Mapping e.g. something parsed by json.loads
    This takes the Python typing hints and applies them (partially) at runtime"""

    # Verify top level manifest has the required keys
    for k in required_keys(OCIManifest):
        if k not in manifest:
            return (None, Exception(f"Manifest {manifest} must contain key {k}"))

    # Verify config in manifest has required keys
    required_descriptor_keys = required_keys(OCIContentDescriptor)
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

    return (typing.cast(OCIManifest, manifest), None)


# mapping of string in the form of a digest to manifests
manifests: Mapping[str, OCIManifest] = {}


@routes.route("OPTIONS", "/manifest")
async def publish_options(request: web.Request) -> web.Response:
    return web.Response(
        headers={
            "Allow": "OPTIONS, POST",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "86400",
        }
    )


@routes.post("/manifest")
async def post_manifest(request: web.Request) -> web.Response:
    manifest_json = await request.json()
    (manifest, error) = build_manifest(manifest_json)
    if manifest:
        log.info(f"Posted manifest {manifest}")
        config = manifest["config"]
        digest = config["digest"]

        # Issue: mypy reports Unsupported target for indexed assignment ("Mapping[str, OCIManifest]")
        # However tests work. Need to figure out what mypy is unhappy with
        manifests[digest] = manifest  # type: ignore

        return web.json_response({"manifest": manifest})

    return web.json_response({"error": error, "manifest": manifest}, status=400)


@routes.get("/manifest/{manifest_id}")
async def get_manifest(request: web.Request) -> web.Response:
    id = request.match_info["manifest_id"]
    log.info(f"Getting manifest for {id}")

    pool = request.app['conn_pool']
    async with pool.acquire() as con:
        stmt = await con.prepare(
            '''SELECT
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
        manifest_schema_version
        FROM manifest_layers
        WHERE manifest_config_digest = $1
        '''
        )
        manifest = await stmt.fetchval(id)
        if manifest:
            return web.json_response({"manifest": manifest})

    return web.json_response({"message": f"Manifest for {id} not found"}, status=404)


@routes.get("/layer/{layer_id}")
async def get_layer(request: web.Request) -> web.Response:
    layer_id = request.match_info["layer_id"]

    pool = request.app['conn_pool']
    async with pool.acquire() as con:
        stmt = await con.prepare(
            '''SELECT
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
        manifest_schema_version
        FROM manifest_layers
        WHERE digest = $1
        '''
        )
        layer = await stmt.fetchval(layer_id)
        if layer:
            return web.json_response({"layer": layer})
            # response.headers["Content-Type"] = "application/vnd.oci.image.layer.v1.tar+gzip"

    return web.json_response({"message": f"Layer for {layer_id} not found"}, status=404)


@routes.post("/layer/{layer_id}")
async def post_layer(request: web.Request) -> web.Response:
    content_len = request.content_length
    content_type = request.content_type
    layer_id = request.match_info["layer_id"]

    if content_type == "multipart/form-data":
        reader = await request.multipart()
        field = await reader.next()

        filename = field.filename
        log.info(
            f"Uploading file length {content_len} type {content_type} filename {filename} field name {field.name}"
        )
        # You cannot rely on Content-Length if transfer is chunked.
        size = 0
        layer_digest = hashlib.sha256()
        async with aiofiles.open(os.path.join("/layers", filename), mode="wb") as f:
            while True:
                chunk = await field.read_chunk(1048576)
                if not chunk:
                    break
                size += len(chunk)
                layer_digest.update(chunk)
                await f.write(chunk)

    sha256_digest = f"sha256:{layer_digest.hexdigest()}"
    return web.json_response({"upload_digest": sha256_digest, "layer_id": layer_id})


# Typical Kubernetes/Open
# See https://kubernetes.io/docs/reference/using-api/health-checks/ for details
@routes.get("/livez")
async def livez(request: web.Request) -> web.Response:
    return web.Response()


# See https://kubernetes.io/docs/reference/using-api/health-checks/ for details
@routes.get("/readyz")
async def readyz(request: web.Request) -> web.Response:
    pool = request.app['conn_pool']
    is_ready = await pool.fetch("SELECT ts, digest FROM manifest_layers where FALSE")
    log.debug(f"Toy manifest service is ready {is_ready}")
    return web.Response()
