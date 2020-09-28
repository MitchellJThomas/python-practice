#!/usr/bin/env python
import logging

from aiohttp import web

from toy_manifest_service import settings, views

logging.basicConfig(level=logging.INFO)

app = web.Application()
app.add_routes(views.routes)
web.run_app(app, port=settings.PORT)
