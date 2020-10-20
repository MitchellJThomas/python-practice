#!/usr/bin/env python
import logging

from aiohttp import web

from toy_manifest_service import schema, settings, views

logging.basicConfig(level=logging.INFO)

app = web.Application()
app.add_routes(views.routes)
app.cleanup_ctx.append(schema.conn_pool)

logging.info(f"Starting Toy Manifest Service on port {settings.PORT}")
web.run_app(app, port=settings.PORT)
