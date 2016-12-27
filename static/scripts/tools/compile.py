#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Needs to be run in the web2py environment
# python web2py.py -S eden -R applications/eden/static/scripts/tools/compile.py

import s3migration
migrate = s3migration.S3Migration()
migrate.compile()
