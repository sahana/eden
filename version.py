#!/bin/python27/python.exe

import os
import datetime
now = datetime.datetime.today()

version, rest = open("VERSION", "r").read()[1:].split(" ", 1)
output = "r%s (%s)" % (int(version) + 1, str(now)[:-7])
open("VERSION", "w").write(output)
