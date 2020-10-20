import asyncio
import logging

import asyncpg
import pytest
from aiohttp import MultipartWriter, web

from toy_manifest_service import schema, views
from toy_manifest_service.schema import (
    OCIContentDescriptor,
    OCIManifest,
    build_manifest,
)

log = logging.getLogger(__name__)


@pytest.fixture
def cli(loop, aiohttp_client, monkeypatch):
    app = web.Application()
    app.add_routes(views.routes)
    return loop.run_until_complete(aiohttp_client(app))


async def wait_for_db():
    while True:
        try:
            async with asyncpg.create_pool(command_timeout=60) as pool:
                while not await schema.schema_ready(pool):
                    log.info("Waiting for database")
                    await asyncio.sleep(1)
                return True
        except Exception as e:
            log.info(f"While waiting for databse caught exception {e}")
            await asyncio.sleep(1)


@pytest.fixture
def cli_with_db(loop, aiohttp_client, caplog):
    caplog.set_level(logging.INFO)
    log.info("Waiting for database")
    loop.run_until_complete(wait_for_db())
    app = web.Application()
    app.add_routes(views.routes)
    app.cleanup_ctx.append(schema.conn_pool)
    return loop.run_until_complete(aiohttp_client(app))


async def test_manifest_roundtrip(cli_with_db, caplog):
    caplog.set_level(logging.INFO)
    manifest: OCIManifest = {
        "schemaVersion": 2,
        "config": OCIContentDescriptor(
            mediaType="application/vnd.oci.image.config.v1+json",
            size=7023,
            digest="sha256:b5b2b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f432a537bc7",
            annotations={"this": "that"},
            urls=[],
        ),
        "layers": [
            OCIContentDescriptor(
                mediaType="application/vnd.oci.image.layer.v1.tar+gzip",
                size=32654,
                digest="sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0",
                annotations={},
                urls=["https://bitbucket/file1.tar.gz"],
            ),
        ],
        "annotations": {"com.example.key1": "value1", "com.example.key2": "value2"},
        "mediaType": "",
    }

    resp = await cli_with_db.get(f'/manifest/{manifest["config"]["digest"]}')
    assert resp.status == 404
    get_manifest = await resp.json()
    assert get_manifest["manifest_id"] == manifest["config"]["digest"]
    assert get_manifest["message"]

    with MultipartWriter("mixed") as mpwriter:
        mpwriter.append_json(manifest)
        resp = await cli_with_db.post("/manifest", data=mpwriter)

    assert resp.status == 200, f"Error message {await resp.text()}"
    message = await resp.json()
    assert message["message"]
    assert message["timestamp"]
    assert message["manifest_digest"] == manifest["config"]["digest"]

    resp = await cli_with_db.get(f'/manifest/{manifest["config"]["digest"]}')
    assert resp.status == 200
    get_manifest = await resp.json()
    assert get_manifest["manifest"] == manifest


async def test_multiple_posts(cli_with_db, caplog):
    caplog.set_level(logging.INFO)
    manifest: OCIManifest = {
        "schemaVersion": 2,
        "config": OCIContentDescriptor(
            mediaType="application/vnd.oci.image.config.v1+json",
            size=5555,
            digest="sha256:0002b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f432a537000",
            annotations={},
            urls=[],
        ),
        "layers": [
            OCIContentDescriptor(
                mediaType="application/vnd.oci.image.layer.v1.tar+gzip",
                size=77777,
                digest="sha256:1234876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee123",
                annotations={},
                urls=["https://bitbucket/file1.tar.gz"],
            ),
        ],
        "annotations": {},
        "mediaType": "",
    }

    with MultipartWriter("mixed") as mpwriter:
        mpwriter.append_json(manifest)
        resp = await cli_with_db.post("/manifest", data=mpwriter)

    assert resp.status == 200, f"Error message {await resp.text()}"
    message = await resp.json()
    assert message["manifest_digest"] == manifest["config"]["digest"]
    assert message["message"]
    assert message["timestamp"]

    with MultipartWriter("mixed") as mpwriter:
        mpwriter.append_json(manifest)
        resp = await cli_with_db.post("/manifest", data=mpwriter)

    assert resp.status == 200, f"Error message {await resp.text()}"
    message = await resp.json()
    assert message.get("manifest_digest") == manifest["config"]["digest"]


async def test_manifest_validation_good_manifest():
    manifest = OCIManifest(
        schemaVersion=2,
        mediaType="manifest_media",
        config=OCIContentDescriptor(
            mediaType="media_thingy",
            digest="sha256:deadbeefx0000",
            size=42,
            urls=None,
            annotations=None,
        ),
        layers=[
            OCIContentDescriptor(
                mediaType="layer_media_thingy",
                digest="sha256:abc123",
                size=2,
                urls=None,
                annotations=None,
            )
        ],
        annotations={
            "com.me.group": "machine learning",
            "com.them.group": "money handler",
        },
    )

    built_manifest, error = build_manifest(manifest)
    assert error is None
    assert manifest == built_manifest


async def test_manifest_validation_empty_manifest():
    manifest = {}

    built_manifest, error = build_manifest(manifest)
    assert type(error) is Exception
    assert "must contain key" in str(error)
    assert built_manifest is None


async def test_manifest_validation_bad_schema_version():
    manifest = {
        "schemaVersion": 86,
        "config": OCIContentDescriptor(
            mediaType="media_thingy",
            digest="sha256:deadbeefx0000",
            size=42,
            urls=None,
            annotations=None,
        ),
        "layers": [
            OCIContentDescriptor(
                mediaType="layer_media_thingy",
                digest="sha256:abc123",
                size=2,
                urls=None,
                annotations=None,
            )
        ],
    }

    built_manifest, error = build_manifest(manifest)
    assert type(error) is Exception
    assert "schemaVersion must be 2" in str(error)
    assert built_manifest is None


async def test_health_endpoints(cli_with_db, caplog):
    caplog.set_level(logging.INFO)
    resp = await cli_with_db.get("/livez")
    assert resp.status == 200

    resp = await cli_with_db.get("/readyz")
    assert resp.status == 200
