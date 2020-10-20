import hashlib
import logging
import os

import aiofiles
from aiohttp import hdrs, web

from .schema import build_manifest, insert_manifest, schema_ready, select_manifest

log = logging.getLogger(__name__)

routes = web.RouteTableDef()


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

    content_type = request.content_type
    expected_type = "multipart/mixed"
    if content_type != expected_type:
        return web.json_response(
            {"message": f"Expecting {expected_type} not {content_type}"}, status=400
        )

    reader = await request.multipart()
    pool = request.app["conn_pool"]
    manifest_digest = ""
    timestamp = ""
    async with pool.acquire() as conn:
        async with conn.transaction():
            while part := await reader.next():
                content_type = part.headers[hdrs.CONTENT_TYPE]

                if content_type == "application/json":
                    manifest_json = await part.json()
                    (manifest, error) = build_manifest(manifest_json)
                    if error:
                        web.json_response(
                            {"error": error, "manifest": manifest}, status=400
                        )

                    if manifest:
                        log.info(f"Got manifest {manifest}")
                        manifest_digest = manifest["config"]["digest"]
                        (timestamp, error) = await insert_manifest(conn, manifest)
                        if error:
                            web.json_response(
                                {"error": str(error), "manifest": manifest}, status=400
                            )

                elif content_type == "application/vnd.oci.image.layer.v1.tar+gzip":
                    filename = part.filename

                    log.info(
                        f"Uploading layer type {content_type} filename {filename} field name {part.name}"
                    )
                    size = 0
                    async with aiofiles.open(
                        os.path.join("/layers", filename), mode="wb"
                    ) as f:
                        while chunk := await part.read_chunk(1048576):
                            size += len(chunk)
                            await f.write(chunk)
                    log.info(f"Wrote {size} bytes to file {filename}")

    return web.json_response(
        {
            "message": "Manifest successfully posted",
            "manifest_digest": manifest_digest,
            "timestamp": timestamp,
        }
    )


@routes.get("/manifest/{manifest_id}")
async def get_manifest(request: web.Request) -> web.Response:
    id = request.match_info["manifest_id"]
    log.info(f"Getting manifest for {id}")

    pool = request.app["conn_pool"]
    async with pool.acquire() as conn:
        (manifest, error) = await select_manifest(conn, id)
        if manifest:
            return web.json_response({"manifest": manifest})
        return web.json_response(
            {
                "message": f"Manifest for {id} not found",
                "manifest_id": id,
                "error": error,
            },
            status=404,
        )


@routes.get("/layer/{layer_id}")
async def get_layer(request: web.Request) -> web.Response:
    layer_id = request.match_info["layer_id"]

    if False:
        response = web.json_response({"layer": layer_id})
        response.headers["Content-Type"] = "application/vnd.oci.image.layer.v1.tar+gzip"
        return response

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
    pool = request.app["conn_pool"]
    if is_ready := await schema_ready(pool):
        log.debug(f"Toy manifest service is ready {is_ready}")
        return web.Response()
    return web.Response(status=503)
