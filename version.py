#!/bin/python

import datetime
import subprocess

now = datetime.datetime.today()

version = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()

output = "eden-dev-%s (%s)" % (version, str(now)[:-7])
open("VERSION", "w").write(output)
