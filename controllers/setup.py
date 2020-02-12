# -*- coding: utf-8 -*-

"""
    Setup Tool:
        Assists with Installation, Configuration & Maintenance of a Deployment
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

if not auth.s3_has_role("ADMIN"):
        auth.permission.fail()

# -----------------------------------------------------------------------------
def index():
    """ Show the index """

    dtable = s3db.setup_deployment
    exists = db(dtable.id > 0).select(dtable.id,
                                      limitby = (0, 1),
                                      )
    if exists:
        # Redirect to the list of monitoring tasks
        redirect(URL(c="setup", f="monitor_task"))
    else:
        templates = settings.get_template()
        if templates == "setup":
            # User-friendly index page to step through deploying Eden
            return {}
        else:
            # Import the current deployment
            country = None
            if isinstance(templates, list):
                for template in templates:
                    try:
                        country = template.split("locations.", 1)[1]
                    except IndexError:
                        continue
                    else:
                        break
                if country:
                    templates.remove("locations.%s" % country)
            deployment_id = s3db.setup_deployment.insert(# @ToDo: Read from .git
                                                         #repo_url = ,
                                                         country = country,
                                                         template = templates,
                                                         db_password = settings.database.get("password"),
                                                         )
            # @ToDo: Support multi-host deployments
            server_id = s3db.setup_server.insert(deployment_id = deployment_id,
                                                 host_ip = "127.0.0.1",
                                                 )
            s3db.setup_monitor_server.insert(server_id = server_id)
            task_id = current.s3task.run_async("dummy")
            instance_id = s3db.setup_instance.insert(deployment_id = deployment_id,
                                                     url = settings.get_base_public_url(),
                                                     sender = settings.get_mail_sender(),
                                                     task_id = task_id,
                                                     )
            s3db.setup_instance_settings_read(instance_id, deployment_id)

            # Redirect to this Deployment's Instances
            redirect(URL(c="setup", f="deployment",
                         args = [deployment_id, "instance"]))

# -----------------------------------------------------------------------------
def aws_cloud():

    return s3_rest_controller(#rheader = s3db.setup_rheader,
                              )

# -----------------------------------------------------------------------------
def gandi_dns():

    return s3_rest_controller(#rheader = s3db.setup_rheader,
                              )

# -----------------------------------------------------------------------------
def deployment():

    def prep(r):
        if r.interactive:
            if r.component:

                # No new servers once deployment is created
                #s3db.configure("setup_server",
                #               insertable = False
                #               )

                # Check if no scheduler task is pending
                #itable = s3db.setup_instance
                #sctable = db.scheduler_task
                #query = (itable.deployment_id == r.id) & \
                #        ((sctable.status != "COMPLETED") & \
                #        (sctable.status  != "FAILED")) & \
                #        (itable.task_id == sctable.id)

                #exists = db(query).select(itable.task_id,
                #                          limitby = (0, 1)
                #                          ).first()

                #if exists:
                #    # Disable creation of new instances
                #    s3db.configure("setup_instance",
                #                   insertable = False
                #                   )

                cname = r.component.name
                if cname == "server":

                    from s3 import S3SQLCustomForm

                    deployment = r.record
                    if deployment.cloud_id:
                        # Assume AWS for now
                        crud_form = S3SQLCustomForm("name",
                                                    "host_ip",
                                                    "role",
                                                    "remote_user",
                                                    "private_key",
                                                    (T("AWS Region"), "aws_server.region"),
                                                    (T("AWS Instance Type"), "aws_server.instance_type"),
                                                    (T("AWS Image"), "aws_server.image"),
                                                    (T("AWS Security Group"), "aws_server.security_group"),
                                                    (T("AWS Instance ID"), "aws_server.instance_id"),
                                                    (T("Monitor"), "monitor_server.enabled"),
                                                    "monitor_server.status",
                                                    )

                        list_fields = ["deployment_id",
                                       "name",
                                       "host_ip",
                                       "role",
                                       "monitor_server.enabled",
                                       "monitor_server.status",
                                       ]
                    else:
                        # No Cloud
                        f = s3db.setup_server.host_ip
                        f.requires = f.requires.other # IP is required
                        crud_form = S3SQLCustomForm("name",
                                                    "host_ip",
                                                    "role",
                                                    "remote_user",
                                                    "private_key",
                                                    (T("Monitor"), "monitor_server.enabled"),
                                                    "monitor_server.status",
                                                    )

                        list_fields = ["deployment_id",
                                       "name",
                                       "host_ip",
                                       "role",
                                       "monitor_server.enabled",
                                       "monitor_server.status",
                                       ]

                    s3db.configure("setup_server",
                                   crud_form = crud_form,
                                   deletable = False, # currently we just support a single server per deployment with Role 'all'
                                   insertable = False, # currently we just support a single server per deployment with Role 'all'
                                   list_fields = list_fields,
                                   )

                    # Has this deployment got a deployed instance?
                    itable = s3db.setup_instance
                    query = (itable.deployment_id == deployment.id) & \
                            (itable.task_id != None)
                    instances = db(query).select(itable.id)
                    if len(instances):
                        # Prevent editing fields
                        stable = s3db.setup_server
                        stable.name.writable = False # @ToDo: Allow switching post-deployment
                        stable.host_ip.writable = False # @ToDo: Allow switching post-deployment
                        if deployment.cloud_id:
                            # Assume AWS for now
                            astable = s3db.setup_aws_server
                            astable.region.writable = False # @ToDo: Allow switching post-deployment
                            astable.instance_type.writable = False # @ToDo: Allow switching post-deployment (Highest Priority)
                            astable.image.writable = False # @ToDo: Allow switching post-deployment
                            astable.security_group.writable = False # @ToDo: Allow switching post-deployment

                elif cname == "instance":
                    if r.component_id:
                        itable = db.setup_instance
                        crecord = db(itable.id == r.component_id).select(itable.task_id,
                                                                         limitby = (0, 1)
                                                                         ).first()
                        if crecord.task_id is not None:
                            # Prevent editing fields
                            itable.type.writable = False # @ToDo: Allow switching post-deployment
                            itable.url.writable = False # @ToDo: Allow switching post-deployment
                            #itable.sender.writable = False # Changes handled in setup_instance_update_onaccept
                            #itable.start.writable = False # Changes handled in setup_instance_update_onaccept

                    elif r.method in (None, "create"):
                        itable = db.setup_instance
                        # Additional instances off by default
                        itable.start.default = False
                        # Remove already-deployed instances from dropdown
                        sctable = db.scheduler_task
                        query = (itable.deployment_id == r.id) & \
                                (sctable.status == "COMPLETED")

                        rows = db(query).select(itable.type,
                                                join = itable.on(itable.task_id == sctable.id)
                                                )
                        types = {1: "prod",
                                 2: "setup",
                                 3: "test",
                                 4: "demo",
                                 }
                        for row in rows:
                            del types[row.type]

                        itable.type.requires = IS_IN_SET(types)

                elif cname == "setting":
                    f = s3db.setup_setting.instance_id
                    f.requires = IS_ONE_OF(db, "setup_instance.id",
                                           f.represent,
                                           filterby = "deployment_id",
                                           filter_opts = [r.id],
                                           sort = True
                                           )

                elif cname == "monitor_task":
                    f = s3db.setup_monitor_task.server_id
                    f.requires = IS_ONE_OF(db, "setup_server.id",
                                           f.represent,
                                           filterby = "deployment_id",
                                           filter_opts = [r.id],
                                           sort = True
                                           )

            elif r.method == "create":

                # Dynamically update list of templates when repo is changed
                s3.scripts.append("/%s/static/scripts/S3/s3.setup.js" % appname)

                try:
                    import requests
                except ImportError:
                    response.warning = T("Cannot download list of templates from remote repo, so using list from this install")
                else:
                    # Download list of templates from remote repo
                    # - currently assumes that repo is hosted on GitHub!
                    table = s3db.setup_deployment
                    parts = table.repo_url.default.split("/")
                    repo_owner = parts[3]
                    repo = parts[4]
                    templates_url = "https://raw.githubusercontent.com/%s/%s/master/modules/templates/templates.json" % \
                    (repo_owner, repo)
                    try:
                        r_request = requests.get(templates_url, timeout=3)
                    except requests.exceptions.RequestException:
                        response.warning = T("Cannot download list of templates from remote repo, so using list from this install")
                    else:
                        import json
                        try:
                            templates = json.loads(r_request.text)
                        except JSONDecodeError:
                            response.warning = T("Cannot download list of templates from remote repo, so using list from this install")
                        else:
                            table.template.requires = IS_IN_SET(templates)

                def deployment_create_postprocess(form):
                    form_vars_get = form.vars.get
                    deployment_id = form_vars_get("id")
                    # Set server name
                    stable = s3db.setup_server
                    url = form_vars_get("sub_production_url")
                    server_vars = {"name": url.split("//")[1].split(".")[0],
                                   }
                    cloud_id = form_vars_get("cloud_id")
                    if cloud_id:
                        # Create AWS Server record
                        server = db(stable.deployment_id == deployment_id).select(stable.id,
                                                                                  limitby = (0, 1)
                                                                                  ).first()
                        s3db.setup_aws_server.insert(server_id = server.id)
                    elif form_vars_get("sub_production_server_host_ip") is None:
                        server_vars["host_ip"] = "127.0.0.1"
                    db(stable.deployment_id == deployment_id).update(**server_vars)

                # Include Production Instance & Server details in main form
                from s3 import S3SQLCustomForm
                crud_form = S3SQLCustomForm((T("Production URL"), "production.url"),
                                            "country",
                                            "template",
                                            "template_manual",
                                            "production.sender",
                                            "webserver_type",
                                            "db_type",
                                            "repo_url",
                                            "cloud_id",
                                            "dns_id",
                                            "production_server.host_ip",
                                            "production_server.remote_user",
                                            "production_server.private_key",
                                            postprocess = deployment_create_postprocess,
                                            )

                s3db.configure("setup_deployment",
                               crud_form = crud_form,
                               )
            else:
                # Has this deployment got a deployed instance?
                itable = s3db.setup_instance
                query = (itable.deployment_id == r.id) & \
                        (itable.task_id != None)
                instances = db(query).select(itable.id)
                if len(instances):
                    # Prevent editing fields
                    table = s3db.setup_deployment
                    table.repo_url.writable = False # @ToDo: Allow switching post-deployment (Highest Priority)
                    table.repo_url.comment = None
                    table.country.writable = False # @ToDo: Allow switching post-deployment
                    table.country.comment = None
                    table.template.writable = False # @ToDo: Allow switching post-deployment
                    table.template_manual.writable = False # @ToDo: Allow switching post-deployment
                    table.template_manual.comment = None
                    table.webserver_type.writable = False # @ToDo: Allow switching post-deployment
                    table.webserver_type.comment = None
                    table.db_type.writable = False # @ToDo: Allow switching post-deployment
                    table.db_type.comment = None
                    table.cloud_id.writable = False # @ToDo: Allow switching post-deployment
                    table.dns_id.writable = False # @ToDo: Allow switching post-deployment

        return True
    s3.prep = prep

    def postp(r, output):
        component = r.component
        if component is None:
            #if r.id and r.method in (None, "read") and "item" in output:
            #    # Get scheduler status for the last queued task
            #    itable = db.setup_instance
            #    sctable = db.scheduler_task

            #    query = (db.setup_instance.deployment_id == r.id)
            #    row = db(query).select(sctable.id,
            #                           sctable.status,
            #                           join = itable.on(itable.task_id == sctable.id),
            #                           orderby = itable.task_id
            #                           ).last()
            #    if row:
            #        item_append = output["item"][0].append
            #        item_append(TR(TD(LABEL("Status"), _class="w2p_fl")))
            #        item_append(TR(TD(row.status)))
            #        if row.status == "FAILED":
            #            resource = s3db.resource("scheduler_run")
            #            task = db(resource.table.task_id == row.id).select().first()
            #            item_append(TR(TD(LABEL("Traceback"), _class="w2p_fl")))
            #            item_append(TR(TD(task.traceback)))
            #            item_append(TR(TD(LABEL("Output"), _class="w2p_fl")))
            #            item_append(TR(TD(task.run_output)))
            pass

        else:
            cname = component.name
            if cname == "instance" and r.method in (None, "read"):
                # Normal Action Buttons
                s3_action_buttons(r)
                # Custom Action Buttons
                table = component.table
                deployment_id = r.id
                query = (table.deployment_id == deployment_id) & \
                        (table.deleted == False)
                rows = db(query).select(table.id,
                                        table.task_id,
                                        table.type,
                                        )
                restrict_d = [str(row.id) for row in rows if row.task_id is None]
                restrict_s = [str(row.id) for row in rows if row.task_id is not None]
                restrict_c = [str(row.id) for row in rows if row.type in (3, 4)]
                s3.actions += [{"url": URL(c = module,
                                           f = "deployment",
                                           args = [deployment_id, "instance", "[id]", "deploy"],
                                           ),
                                "_class": "action-btn",
                                "label": s3_str(T("Deploy")),
                                "restrict": restrict_d,
                                },
                               {"url": URL(c = module,
                                           f = "deployment",
                                           args = [deployment_id, "instance", "[id]", "settings"],
                                           ),
                                "_class": "action-btn",
                                "label": s3_str(T("Read Settings")),
                                "restrict": restrict_s,
                                },
                               {"url": URL(c = module,
                                           f = "deployment",
                                           args = [deployment_id, "instance", "[id]", "start"],
                                           ),
                                "_class": "action-btn",
                                "label": s3_str(T("Start")),
                                "restrict": restrict_s,
                                },
                               {"url": URL(c = module,
                                           f = "deployment",
                                           args = [deployment_id, "instance", "[id]", "stop"],
                                           ),
                                "_class": "action-btn",
                                "label": s3_str(T("Stop")),
                                "restrict": restrict_s,
                                },
                               {"url": URL(c = module,
                                           f = "deployment",
                                           args = [deployment_id, "instance", "[id]", "clean"],
                                           ),
                                "_class": "action-btn",
                                "label": s3_str(T("Clean")),
                                "restrict": restrict_c,
                                },
                               # @ToDo: Better handled not as an Action Button as this is a rarer, more elaborate workflow
                               #{"url": URL(c = module,
                               #            f = "deployment",
                               #            args = [deployment_id, "instance", "[id]", "upgrade"],
                               #            ),
                               # "_class": "action-btn",
                               # "label": s3_str(T("Upgrade")),
                               # },
                               ]

            elif cname == "setting" and r.method in (None, "read"):
                # Normal Action Buttons
                s3_action_buttons(r)
                # Custom Action Buttons
                table = component.table
                deployment_id = r.id
                query = (table.deployment_id == deployment_id) & \
                        (table.deleted == False)
                rows = db(query).select(table.id,
                                        table.new_value,
                                        )
                restrict_a = [str(row.id) for row in rows if row.new_value is not None]
                s3.actions.append({"url": URL(c = module,
                                              f = "deployment",
                                              args = [deployment_id, "setting", "[id]", "apply"],
                                              ),
                                   "_class": "action-btn",
                                   "label": s3_str(T("Apply")),
                                   "restrict": restrict_a,
                                   })

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.setup_rheader,
                              )

# -----------------------------------------------------------------------------
def server():

    def prep(r):
        if r.interactive:
            if r.record:
                if not r.component:

                    if r.method in ("check", "enable", "disable"):
                        return True

                    deployment_id = r.record.deployment_id
                    if deployment_id:
                        # Open on Deployment Tab
                        redirect(URL(c="setup", f="deployment",
                                     args = [deployment_id, "server", r.id],
                                     ))

                    # 'External' servers just added for Monitoring
                    from s3 import S3SQLCustomForm
                    f = s3db.setup_server.host_ip
                    f.requires = f.requires.other # IP is required
                    crud_form = S3SQLCustomForm("name",
                                                "host_ip",
                                                "role",
                                                "remote_user",
                                                "private_key",
                                                (T("Monitor"), "monitor_server.enabled"),
                                                "monitor_server.status",
                                                )

                    s3db.configure("setup_server",
                                   crud_form = crud_form,
                                   )

            else:
                # No Cloud in create form
                # - we don't deploy Servers except within Deployments
                from s3 import S3SQLCustomForm
                f = s3db.setup_server.host_ip
                f.requires = f.requires.other # IP is required
                crud_form = S3SQLCustomForm(#"deployment_id",
                                            "name",
                                            "host_ip",
                                            "role",
                                            "remote_user",
                                            "private_key",
                                            (T("Monitor"), "monitor_server.enabled"),
                                            "monitor_server.status",
                                            )

                list_fields = ["deployment_id",
                               "name",
                               "host_ip",
                               "role",
                               "monitor_server.enabled",
                               "monitor_server.status",
                               ]

                s3db.configure("setup_server",
                               create_onaccept = None, # Handled by S3SQLCustomForm
                               crud_form = crud_form,
                               #insertable = False, # We want to allow monitoring of external hosts
                               list_fields = list_fields,
                               )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and not r.id:
            # Normal Action Buttons
            #s3_action_buttons(r)
            # Custom Action Buttons
            table = s3db.setup_server
            mtable = s3db.setup_monitor_server
            rows = db(table.deleted == False).select(table.id,
                                                     table.deployment_id,
                                                     mtable.enabled,
                                                     left = mtable.on(mtable.server_id == table.id),
                                                     )
            #restrict_deployment = [str(row.id) for row in rows if row["setup_server.deployment_id"] is not None]
            restrict_external = [str(row["setup_server.id"]) for row in rows if row["setup_server.deployment_id"] is None]
            restrict_enable = [str(row["setup_server.id"]) for row in rows if row.get("setup_monitor_server.enabled") is not True]
            restrict_disable = [str(row["setup_server.id"]) for row in rows if row.get("setup_monitor_server.enabled") is True]
            s3.actions = [{"url": URL(args = "[id]"),
                           "_class": "action-btn",
                           "label": s3_str(T("Open")),
                           },
                          {"url": URL(args = ["[id]", "delete"]),
                           "_class": "delete-btn",
                           "label": s3_str(T("Delete")),
                           "restrict": restrict_external,
                           },
                          {"url": URL(args = ["[id]", "enable"]),
                           "_class": "action-btn",
                           "label": s3_str(T("Enable")),
                           "restrict": restrict_enable,
                           },
                          {"url": URL(args = ["[id]", "disable"]),
                           "_class": "action-btn",
                           "label": s3_str(T("Disable")),
                           "restrict": restrict_disable,
                           },
                          ]
            if not s3task._is_alive():
                # No Scheduler Running (e.g. Windows Laptop)
                s3.actions.append({"url": URL(args = ["[id]", "check"]),
                                   "_class": "action-btn",
                                   "label": s3_str(T("Check")),
                                   })

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.setup_rheader,
                              )

# -----------------------------------------------------------------------------
#def instance():

#    return s3_rest_controller(#rheader = s3db.setup_rheader,
#                              )

# -----------------------------------------------------------------------------
#def setting():

#    return s3_rest_controller(#rheader = s3db.setup_rheader,
#                              )

# -----------------------------------------------------------------------------
def monitor_check():

    def prep(r):
        if r.interactive:
            import inspect
            import sys

            template = settings.get_setup_monitor_template()
            module_name = "applications.%s.modules.templates.%s.monitor" % \
                (appname, template)
            __import__(module_name)
            mymodule = sys.modules[module_name]
            S3Monitor = mymodule.S3Monitor()

            functions = inspect.getmembers(S3Monitor, \
                                           predicate = inspect.isfunction)
            function_opts = []
            append = function_opts.append
            for f in functions:
                f = f[0]
                # Filter out helper functions
                if not f.startswith("_"):
                    append(f)

            s3db.setup_monitor_check.function_name.requires = IS_IN_SET(function_opts,
                                                                        zero = None)

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.setup_rheader,
                              )

# -----------------------------------------------------------------------------
def monitor_run():
    """
        Logs
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def monitor_task():

    from s3 import S3OptionsFilter, s3_set_default_filter

    tablename = "setup_monitor_task"

    filter_widgets = [S3OptionsFilter("enabled",
                                      label = T("Enabled"),
                                      options = {True: T("Yes"),
                                                 False: T("No"),
                                                 },
                                      cols = 2,
                                      ),
                      ]

    s3db.configure(tablename,
                   filter_widgets = filter_widgets,
                   orderby = "setup_monitor_task.status desc",
                   )

    # Only show Enabled Tasks by default
    # @ToDo: Also hide those from disabled Servers
    s3_set_default_filter("~.enabled",
                          lambda selector, tablename: True,
                          tablename = tablename)

    def postp(r, output):
        if r.interactive and not r.id:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            rows = db(table.deleted == False).select(table.id,
                                                     table.enabled,
                                                     )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]
            s3.actions += [{"url": URL(args=["[id]", "enable"]),
                            "_class": "action-btn",
                            "label": s3_str(T("Enable")),
                            "restrict": restrict_e,
                            },
                           {"url": URL(args = ["[id]", "disable"]),
                            "_class": "action-btn",
                            "label": s3_str(T("Disable")),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions.append({"url": URL(args = ["[id]", "check"]),
                                   "_class": "action-btn",
                                   "label": s3_str(T("Check")),
                                   })
        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.setup_rheader,
                              )

# END =========================================================================
