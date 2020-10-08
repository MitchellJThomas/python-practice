#!/usr/bin/env python
import logging

from aiohttp import web

from toy_manifest_service import schema, settings, views

logging.basicConfig(level=logging.INFO)


async def conn_pool(app):
    app['conn_pool'] = await schema.initialize_database()
    yield
    await app['conn_pool'].close()


app = web.Application()
app.add_routes(views.routes)
app.cleanup_ctx.append(conn_pool)

logging.info(f"Starting toy manifest service on port {settings.PORT}")
web.run_app(app, port=settings.PORT)
