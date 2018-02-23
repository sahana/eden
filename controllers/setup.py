# -*- coding: utf-8 -*-

"""
    Setup Tool:
        Assists with Installation of a Deployment
        tbc: Assists with Configuration of a Deployment
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Show the index """

    return {}

# -----------------------------------------------------------------------------
def deployment():

    from s3 import S3SQLCustomForm, S3SQLInlineComponent

    crud_form = S3SQLCustomForm("name",
                                "repo_url",
                                "country",
                                "template",
                                "remote_user",
                                "private_key",
                                "secret_key",
                                "access_key",
                                "webserver_type",
                                "db_type",
                                "db_password",
                                "db_type",
                                "db_password",
                                S3SQLInlineComponent("server",
                                                     label = T("Server Role"),
                                                     fields = ["role", "host_ip", "hostname"],
                                                     ),
                                S3SQLInlineComponent("instance",
                                                     label = T("Instance Type"),
                                                     fields = ["type", "url", "prepop_options"],
                                                     #filterby=dict(field = "type",
                                                                   #options = ["prod", "demo"]
                                                                   #),
                                                     multiple = False,
                                                     ),
                                )

    s3db.configure("setup_deployment",
                   crud_form = crud_form,
                   )

    def prep(r):
        if r.method in ("create", None):
            s3.scripts.append("/%s/static/scripts/S3/s3.setup.js" % appname)

        if r.interactive:
            if r.component and r.id:

                # Set up the prepop options according to the template
                prepop_options = s3db.setup_get_prepop_options(r.record.template)
                db.setup_instance.prepop_options.requires = IS_IN_SET(prepop_options, multiple=True)

                # No new servers once deployment is created
                s3db.configure("setup_server",
                               insertable = False
                               )

                # Check if no scheduler task is pending
                itable = db.setup_instance
                sctable = db.scheduler_task
                query = (itable.deployment_id == r.id) & \
                        ((sctable.status != "COMPLETED") & \
                        (sctable.status  != "FAILED"))

                exists = db(query).select(itable.scheduler_id,
                                          join = itable.on(itable.scheduler_id == sctable.id),
                                          limitby = (0, 1)
                                          ).first()

                if exists:
                    # Disable creation of new instances
                    s3db.configure("setup_instance",
                                   insertable = False
                                   )

                elif r.component.name == "instance":
                    if r.method in (None, "create"):
                        # Remove already-deployed instances from dropdown
                        itable = db.setup_instance
                        sctable = db.scheduler_task
                        query = (itable.deployment_id == r.id) & \
                                (sctable.status == "COMPLETED")

                        rows = db(query).select(itable.type,
                                                join = itable.on(itable.scheduler_id == sctable.id)
                                                )
                        types = {1: "prod",
                                 2: "test",
                                 3: "demo",
                                 }
                        for row in rows:
                            del types[row.type]

                        itable.type.requires = IS_IN_SET(types)
        return True
    s3.prep = prep

    def postp(r, output):
        if r.component is None:
            if r.method in (None, "read") and r.id:
                # get scheduler status for the last queued task
                itable = db.setup_instance
                sctable = db.scheduler_task

                query = (db.setup_instance.deployment_id == r.id)
                row = db(query).select(sctable.id,
                                       sctable.status,
                                       join = itable.on(itable.scheduler_id==sctable.id),
                                       orderby = itable.scheduler_id
                                       ).last()
                item_append = output["item"][0].append
                item_append(TR(TD(LABEL("Status"), _class="w2p_fl")))
                item_append(TR(TD(row.status)))
                if row.status == "FAILED":
                    resource = s3db.resource("scheduler_run")
                    task = db(resource.table.task_id == row.id).select().first()
                    item_append(TR(TD(LABEL("Traceback"), _class="w2p_fl")))
                    item_append(TR(TD(task.traceback)))
                    item_append(TR(TD(LABEL("Output"), _class="w2p_fl")))
                    item_append(TR(TD(task.run_output)))

        elif r.component.name == "instance":
            if r.method in (None, "read"):
                s3.actions = [{"url": URL(c = module,
                                          f = "management",
                                          vars = {"instance": "[id]",
                                                  "type": "clean",
                                                  "deployment": r.id,
                                                  }
                                          ),
                               "_class": "action-btn",
                               "label": "Clean"
                               },
                              {"url": URL(c = module,
                                          f = "management",
                                          vars = {"instance": "[id]",
                                                  "type": "eden",
                                                  "deployment": r.id
                                                  }
                                          ),
                               "_class": "action-btn",
                               "label": "Upgrade Eden"
                               },
                              ]
        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.setup_rheader,
                              )

# -----------------------------------------------------------------------------
def management():
    try:
        _id = get_vars["instance"]
        deployment_id = get_vars["deployment"]
        _type = get_vars["type"]
    except:
        session.error = T("Record Not Found")
        redirect(URL(c="setup", f="index"))

    # Check if management task already running
    exists = s3db.setup_management_exists(_type, _id, deployment_id)

    if exists:
        session.error = T("A management task is running for the instance")
        redirect(URL(c="setup", f="deployment", args=[deployment_id, "instance"]))

    # Check if instance was successfully deployed
    ttable = s3db.scheduler_task
    itable = s3db.setup_instance
    query = (ttable.status == "COMPLETED") & \
            (itable.id == _id)
    success = db(query).select(itable.id,
                               join=ttable.on(ttable.id == itable.scheduler_id),
                               limitby = (0, 1)
                               ).first()

    if success:
        # add the task to scheduler
        current.s3task.schedule_task("setup_management",
                                     args = [_type, _id, deployment_id],
                                     timeout = 3600,
                                     repeats = 1,
                                     )
        session.confirmation = T("Task queued in scheduler")
        redirect(URL(c="setup", f="deployment", args=[deployment_id, "instance"]))
    else:
        session.error = T("The instance was not successfully deployed")
        redirect(URL(c="setup", f="deployment", args=[deployment_id, "instance"]))

# -----------------------------------------------------------------------------
def prepop_setting():

    if request.ajax:
        template = request.post_vars.get("template")
        return json.dumps(s3db.setup_get_prepop_options(template))

# -----------------------------------------------------------------------------
def refresh():

    try:
        id = request.args[0]
    except:
        current.session.error = T("Record Not Found")
        redirect(URL(c="setup", f="index"))

    result = s3db.setup_refresh(id)

    if result["success"]:
        current.session.flash = result["msg"]
        redirect(URL(c="setup", f=result["f"], args=result["args"]))
    else:
        current.session.error = result["msg"]
        redirect(URL(c="setup", f=result["f"], args=result["args"]))

# -----------------------------------------------------------------------------
def upgrade_status():

    if request.ajax:
        record_id = request.post_vars.get("id")
        utable = s3db.setup_upgrade
        stable = s3db.scheduler_task
        query = (utable.deployment_id == record_id)

        row = current.db(query).select(stable.status,
                                       join = utable.on(stable.id == utable.scheduler)
                                       ).last()

        if row.status == "COMPLETED":
            return json.dumps(current.T("Upgrade Completed! Refreshing the page in 5 seconds"))

# END =========================================================================
