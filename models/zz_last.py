# -*- coding: utf-8 -*-

"""
    Final actions before running controllers
"""

# Pass Theme to Compiler
settings.set_theme()

# Empty dict to store custom CRUD views
s3.views = {}

if session.s3.pending_consent and request.controller != "default":
    # Enforce consent response
    redirect(URL(c="default", f="user",
                 args = ["consent"],
                 vars = {"_next": URL(),
                         },
                 ))

if auth.permission.format in ("html",):

    # Should we use Content-Delivery Networks?
    s3.cdn = settings.get_base_cdn()

    # Compose the options menu
    controller = request.controller
    if controller not in s3_menu_dict:
        # No custom menu, so use standard menu for this controller
        menu.options = S3OptionsMenu(controller).menu
        if not menu.options:
            # Fallback to an auto-generated list of resources
            # @ToDo
            pass
            #from eden.layouts import M
            #allmodels = models.__dict__
            #tables = []
            #for name in allmodels:
            #    if name == controller:
            #        for classname in allmodels[name].__all__:
            #            for tablename in models[controller][classname].names:
            #                tables.append(tablename)
            #menu.options = M(c=controller)(
            #    M(resourcename, f=resourcename)(
            #        M("New", m="create"),
            #        M("List All"),
            #    ),
            #)

    else:
        # Use custom menu
        menu.options = s3_menu_dict[controller]

    # Add breadcrumbs
    menu.breadcrumbs = S3OptionsMenu.breadcrumbs

# Re-routed REST controllers
c, f = request.controller, request.function
if f == "rest":
    # Must not be accessed directly
    raise HTTP(404, "invalid controller (%s/%s)" % (c, f))

rest_controllers = settings.get_base_rest_controllers()
if rest_controllers and (c, f) in rest_controllers:
    request.args = [c, f] + request.args
    request.controller, request.function = "custom", "rest"

# END =========================================================================
