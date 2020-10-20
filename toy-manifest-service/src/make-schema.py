#!/usr/bin/env python
import logging

from toy_manifest_service import schema

logging.basicConfig(level=logging.INFO)

print(schema.create_manifest_layers_statement(12))
