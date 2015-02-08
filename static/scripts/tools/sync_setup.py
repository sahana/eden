# Setup Script for Sync:
# - only needed for active sites (sync masters)
# - run after 1st run initialization and after the admin account has been created
# - configure the values below either manually or by config script for the respective instance
#
# Use like:
# (Win32 users prefix the config options with 'set ' & no need to export)
# site_type=active
# export site_type
# ...
# cd /path/to/web2py
# python web2py.py -S <appname> -M -R sync_setup.py

import os
import uuid

# Configuration ===============================================================

# site_type = "active"|"passive"
try:
    site_type = os.environ["site_type"]
except KeyError:
    site_type = "active"

# proxy URL, e.g. "http://proxy.example.com:3128"
try:
    proxy_url = os.environ["proxy_url"]
except KeyError:
    proxy_url = None

# Passive site URL (required)
try:
    passive_site_url = os.environ["passive_site_url"]
except KeyError:
    passive_site_url = "http://www.example.com/eden"

# Passive site admin username and password
try:
    passive_site_username = os.environ["passive_site_username"]
except KeyError:
    passive_site_username = "admin@example.com"
try:
    passive_site_password = os.environ["passive_site_password"]
except KeyError:
    passive_site_password = "testing"

# Resource names (master table names)
try:
    resources = [ os.environ["sync_resources_1"] ]
except KeyError:
    resources = [
                # Include all non-component resources
                "pr_person",
                "org_organisation",
                "org_office",
                "req_req"
            ]
else:
    for i in range(2, 500):
        try:
            resources.append(os.environ["sync_resources_%i" % i])
        except KeyError:
            break

# Synchronization interval, minutes
try:
    sync_interval = int(os.environ["sync_interval"])
except KeyError:
    sync_interval = 2

# End of configuration options ================================================

# Load models
if site_type == "active":

    # Settings
    sync_config = s3db.sync_config
    config = Storage(proxy=proxy_url)
    record = db(sync_config.id!=None).select(sync_config.id, limitby=(0, 1)).first()
    if record:
        record.update_record(**config)
    else:
        sync_config.insert(**config)

    # Repository
    sync_repository = db.sync_repository
    repository = Storage(name="Passive",
                         url=passive_site_url,
                         username=passive_site_username,
                         password=passive_site_password)
    q = (sync_repository.name == repository.name)
    record = db(q).select(sync_repository.id, limitby=(0, 1)).first()
    if record:
        repository_id = record.id
        repository.update(deleted=False)
        record.update_record(**repository)
    else:
        repository_id = sync_repository.insert(**repository)
        repository.id = repository_id

    if not repository_id:
        raise RuntimeError("Cannot register or update peer repository")
    else:
        success = s3base.S3Sync().request_registration(repository)
        if not success:
            print >>sys.stderr, "Could not auto-register repository, please register manually"

    # Resources
    sync_policies = s3base.S3ImportItem.POLICY
    sync_task = db.sync_task
    for resource_name in resources:
        task = Storage(resource_name=resource_name,
                       repository_id=repository_id)
        q = (sync_task.repository_id == repository_id) & \
            (sync_task.resource_name == resource_name)
        record = db(q).select(sync_repository.id, limitby=(0, 1)).first()
        if record:
            task.update(deleted=False)
            record.update_record(**task)
        else:
            sync_task.insert(**task)

    # Scheduler task
    task = str(uuid.uuid4())
    function_name="sync_synchronize"
    args = [repository_id]
    repeats = 0
    period = sync_interval * 60
    timeout = 600

    gtable = db.auth_membership
    query = (gtable.group_id == ADMIN) # & (gtable.deleted != True)
    record = db(query).select(gtable.user_id, limitby=(0, 1)).first()
    vars = dict()
    if record:
        vars.update(user_id = record.user_id)

    now = datetime.datetime.now()
    then = now + datetime.timedelta(days=365)
    scheduler_task_id = current.s3task.schedule_task(task,
                                                     function_name=function_name,
                                                     args=args,
                                                     vars=vars,
                                                     start_time=now,
                                                     stop_time=then,
                                                     repeats=repeats,
                                                     period=period,
                                                     timeout=timeout,
                                                     ignore_duplicate=False)

    # Job link
    if scheduler_task_id:
        sync_job = db.sync_job
        job = Storage(repository_id=repository_id,
                      scheduler_task_id=scheduler_task_id)
        record = db().select(sync_job.id, limitby=(0, 1)).first()
        if record:
            record.update_record(**job)
        else:
            sync_job.insert(**job)

db.commit()
