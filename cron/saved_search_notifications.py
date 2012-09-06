import sys
from eden.msg import search_subscription_notifications

current.auth.s3_impersonate("admin@example.com")

if sys.argv:
    search_subscription_notifications(sys.argv[1])
