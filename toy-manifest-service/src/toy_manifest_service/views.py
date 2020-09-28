import hashlib
import json
import logging
import os
import urllib.parse as url
from typing import Mapping, Optional, Set, TypedDict

import aiofiles
from aiohttp import web

log = logging.getLogger(__name__)

routes = web.RouteTableDef()

OCIContentDescriptor = TypedDict(
    'OCIContentDescriptor',
    {
        # REQUIRED Media type values MUST comply with RFC 6838,
        # including the naming requirements in its section
        # 4.2. including OCI types found in mime.types taken from
        # https://github.com/opencontainers/image-spec/blob/master/descriptor.md
        'mediaType': str,
        # Digest values following the form
        # https://github.com/opencontainers/image-spec/blob/master/descriptor.md#digests
        # digest                ::= algorithm ":" encoded
        # algorithm ::= algorithm-component
        #   (algorithm-separator algorithm-component)*
        # algorithm-component   ::= [a-z0-9]+
        # algorithm-separator   ::= [+._-]
        # encoded               ::= [a-zA-Z0-9=_-]+
        # REQUIRED Registered Algorithms are "sha512" and "sha256"
        'digest': str,
        # REQUIRED Size should accomodate int64. Python3 int's can
        # indeed do that e.g. int.bit_length(pow(2, 63))
        'size': Optional[int],
        # OPTIONAL urls specifies a list of URIs from which this
        # object MAY be downloaded. Each entry MUST conform to RFC
        # 3986. Entries SHOULD use the http and https schemes, as
        # defined in RFC 7230.
        'urls': Optional[Set[url.ParseResult]],
        # OPTIONAL annotations follows the rules outlined here
        # https://github.com/opencontainers/image-spec/blob/master/annotations.md#rules
        'annotations': Optional[Mapping[str, str]],
    },
)

OCIManifest = TypedDict(
    'OCIManifest',
    {
        # This REQUIRED property specifies the image manifest schema
        # version. For this version of the specification, this MUST be
        # 2 to ensure backward compatibility with older versions of
        # Docker. The value of this field will not change. This field
        # MAY be removed in a future version of the
        # specification. Taken from
        # https://github.com/opencontainers/image-spec/blob/master/manifest.md
        'schemaVersion': int,
        # This property is reserved for use, to maintain
        # compatibility. When used, this field contains the media type
        # of this document, which differs from the descriptor use of
        # mediaType.
        'mediaType': str,
        # This REQUIRED property references a configuration object for
        # a container, by digest.
        'config': OCIContentDescriptor,
        # This OPTIONAL property contains arbitrary metadata for the
        # image manifest.
        'annotations': Optional[Mapping[str, str]],
    },
)


@routes.route('OPTIONS', '/manifest')
async def publish_options(request: web.Request) -> web.Response:
    return web.Response(
        headers={
            'Allow': 'OPTIONS, POST',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '86400',
        }
    )


@routes.post('/manifest')
async def post_manifest(request: web.Request) -> web.Response:
    body = await request.text()
    install_request = json.loads(body)
    log.info('Install request %s', body)

    host = install_request.get('schemaVersion')
    if not host:
        return web.Response(text=f"Agent IP required {body}", status=400)

    response = web.Response(text=body)
    response.headers['Access-Control-Allow-Origin'] = '*'

    # run_multiple_clients([{'host': host}])
    return response


@routes.get('/manifest/{manifest_id}')
async def get_manifest(request: web.Request) -> web.Response:
    id = request.match_info['manifest_id']
    log.info(f"Getting {id}")

    response = web.json_response([])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@routes.get('/layer/{layer_id}')
async def get_layer(request: web.Request) -> web.Response:
    request.match_info['layer_id']

    response = web.json_response([])
    response.headers['Content-Type'] = 'application/vnd.oci.image.layer.v1.tar+gzip'
    return response


@routes.post('/layer/{layer_id}')
async def post_layer(request: web.Request) -> web.Response:
    content_len = request.content_length
    content_type = request.content_type
    layer_id = request.match_info['layer_id']

    if content_type == 'multipart/form-data':
        reader = await request.multipart()
        field = await reader.next()

        filename = field.filename
        log.info(
            f'Uploading file length {content_len} type {content_type} filename {filename} field name {field.name}'
        )
        # You cannot rely on Content-Length if transfer is chunked.
        size = 0
        layer_digest = hashlib.sha256()
        async with aiofiles.open(os.path.join('/layers', filename), mode='wb') as f:
            while True:
                chunk = await field.read_chunk(1048576)
                if not chunk:
                    break
                size += len(chunk)
                layer_digest.update(chunk)
                await f.write(chunk)

    sha256_digest = f"sha256:{layer_digest.hexdigest()}"
    return web.json_response({"upload_digest": sha256_digest, "layer_id": layer_id})
