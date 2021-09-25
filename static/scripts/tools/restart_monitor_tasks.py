#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Script to reset all Monitor Tasks on all Enabled Servers
#
# Run as:
#   python web2py.py --no-banner -S eden -M -R applications/eden/static/scripts/tools/restart_monitor_tasks.py

output = s3db.setup_monitor_task_restart()
db.commit()
print(output)
