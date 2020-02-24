#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Script to check the status of the Scheduler Worker
#
# Run as:
#   python web2py.py --no-banner -S eden -M -R applications/eden/static/scripts/tools/check_scheduler.py -A earliest

import datetime
import sys

# Parse Arguments
# argv[0] is the script name
try:
    earliest = sys.argv[1]
except IndexError:
    print("No earliest supplied")
    sys.exit(2)

wtable = s3db.scheduler_worker
worker = db(wtable.status == "ACTIVE").select(wtable.last_heartbeat,
                                              limitby = (0, 1)
                                              ).first()

if worker is None:
    print("Warning: Scheduler not ACTIVE")

elif worker.last_heartbeat < datetime.datetime.fromisoformat(earliest):
    print("Warning: Scheduler stalled since %s" % worker.last_heartbeat.strftime("%H:%M %a %d %b"))
