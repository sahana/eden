# -*- coding: utf-8 -*-

"""
    Final actions before running controllers
"""

# Pass Theme to Compiler
s3.theme = settings.get_theme()

if auth.permission.format in ("html"):

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


