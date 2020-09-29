import json

import pytest
from aiohttp import web

from toy_manifest_service import views
from toy_manifest_service.views import OCIContentDescriptor, OCIManifest, build_manifest


@pytest.fixture
def cli(loop, aiohttp_client, monkeypatch):
    app = web.Application()
    app.add_routes(views.routes)
    return loop.run_until_complete(aiohttp_client(app))


async def test_manifest_roundtrip(cli):
    manifest: views.OCIManifest = {
        "schemaVersion": 2,
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "size": 7023,
            "digest": "sha256:b5b2b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f432a537bc7",
        },
        "layers": [
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "size": 32654,
                "digest": "sha256:9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0",
            },
        ],
        "annotations": {"com.example.key1": "value1", "com.example.key2": "value2"},
    }
    resp = await cli.post('/manifest', data=json.dumps(manifest))
    assert resp.status == 200
    message = await resp.json()
    assert message["manifest"] == manifest

    resp = await cli.get(f'/manifest/{manifest["config"]["digest"]}')
    assert resp.status == 200
    get_manifest = await resp.json()
    assert get_manifest["manifest"] == manifest


async def test_manifest_validation():
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

    assert manifest == build_manifest(manifest)
