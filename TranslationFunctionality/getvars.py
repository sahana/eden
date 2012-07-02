import sys
from gluon import current

# Get current settings
settings = current.deployment_settings

# Get variable names
varnames=sys.argv[1:]

for v in varnames:
    
    v = v.replace("current.deployment_settings","settings")
    v = v.replace("()",'')
    l = v.split('.')
    obj = settings

    # Getting the actual value of the variable
    for atr in l[1:]:
      obj = getattr(obj,atr)()
    print obj
