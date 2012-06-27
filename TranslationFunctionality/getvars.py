import sys
from gluon import current


settings = current.deployment_settings

varnames=sys.argv

for v in varnames[1:]:
    
    v = v.replace("current.deployment_settings","settings")
    v = v.replace("()",'')
    l = v.split('.')
    obj = settings
    for atr in l[1:]:
      obj = getattr(obj,atr)()
    print obj
