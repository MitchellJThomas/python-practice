import json
import logging
from typing import TypedDict

from aiohttp import web

log = logging.getLogger(__name__)

routes = web.RouteTableDef()

AgentStatus = TypedDict(
    'AgentStatus',
    {
        'agentIP': str,
        'agentType': str,
        'agentVersion': str,
        'consoleIP': str,
        'status': str,
    },
)


@routes.route('OPTIONS', '/installAgent')
async def publish_options(request: web.Request) -> web.Response:
    return web.Response(
        headers={
            'Allow': 'OPTIONS, POST',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '86400',
        }
    )


@routes.post('/installAgent')
async def publish(request: web.Request) -> web.Response:
    body = await request.text()
    install_request = json.loads(body)
    log.info('Install request %s', body)

    host = install_request.get('agentIP')
    if not host:
        return web.Response(text=f"Agent IP required {body}", status=400)

    password = install_request.get('password')
    if not password:
        return web.Response(text=f"Password required {body}", status=400)

    user = install_request.get('userName')
    if not user:
        return web.Response(text=f"User required {body}", status=400)

    consoleIP = install_request.get('consoleIP')
    if not consoleIP:
        return web.Response(text=f"Console IP required {body}", status=400)

    response = web.Response(text=body)
    response.headers['Access-Control-Allow-Origin'] = '*'

    # run_multiple_clients([{'host': host}])
    return response


@routes.get('/getAgent')
async def receive(request: web.Request) -> web.Response:
    # return web.HTTPNotFound()
    response = web.json_response([])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
