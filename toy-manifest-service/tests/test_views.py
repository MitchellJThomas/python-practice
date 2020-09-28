import json

import pytest
from agent_manager import views
from aiohttp import web


@pytest.fixture
def cli(loop, aiohttp_client, monkeypatch):
    app = web.Application()
    app.add_routes(views.routes)
    return loop.run_until_complete(aiohttp_client(app))


async def test_roundtrip(cli):
    resp = await cli.post('/installAgent', data=json.dumps([]))
    assert resp.status == 200
    assert resp.headers['Access-Control-Allow-Origin'] == '*'

    resp = await cli.get('/getAgent')
    assert resp.status == 200
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    message = await resp.json()
    assert message.status == 200
