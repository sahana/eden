# -*- coding: utf-8 -*-

# File needs to be last in order to be able to have all Tables defined

# -----------------------------------------------------------------------------
# GIS config
# -----------------------------------------------------------------------------

from gluon import *
request = current.request
reponse = current.response
session = current.session
db = current.db
manager = current.manager
deployment_settings = current.deployment_settings
gis = current.gis

# Pass Tasks to global scope
response.s3.download_kml = download_kml

if request.vars._config:
    # The user has just selected a config from the GIS menu
    try:
        config = int(request.vars._config)
    except ValueError:
        # Manually-crafted URL?
        pass
    else:
        session.s3.gis_config_id = config
        if deployment_settings.has_module("event"):
            # See if this config is associated with an Event
            manager.load("event_event")
            table = db.event_config
            query = (table.config_id == config)
            event = db(query).select(table.event_id,
                                     limitby=(0, 1)).first()
            if event:
                session.s3.event = event.event_id
            else:
                session.s3.event = None
    # @ToDo: Find out how to get _config off the url that the user will see
    # when the next page loads. Then do the same for _language.
    del request.vars._config

# Set the field options that depend on the currently selected gis_config,
# and hence on a particular set of labels for the location hierarchy.
gis.set_config(session.s3.gis_config_id, force_update_dependencies=True)

# -----------------------------------------------------------------------------
# GIS menu
# -----------------------------------------------------------------------------
if deployment_settings.get_gis_menu():
    # Substitute the real menu for the placeholder
    gis_index = response.menu.index(s3.gis_menu_placeholder)
    response.menu.pop(gis_index)
    gis_menu = []
    # Use short names for the site and personal configs else they'll wrap.
    gis_menu.append([{"name": T("Default Map"),
                      "id": "region_id_1",
                      "value": session.s3.gis_config_id == 1,
                      "request_type": "load"},
                      False,
                      URL(args=request.args,
                          vars={"_config":1})])
    ctable = db.gis_config
    if auth.user:
        query = (ctable.pe_id == auth.user.pe_id)
        personal_config = db(query).select(ctable.id,
                                           limitby=(0, 1)).first()
        if personal_config:
            gis_menu.append(
                [{"name": T("Personal Map"),
                  "id": "region_id_%s" % personal_config.id,
                  "value": session.s3.gis_config_id == personal_config.id,
                  "request_type": "load"},
                 False,
                 URL(args=request.args,
                     vars={"_config":personal_config.id})])
    else:
        personal_config = None

    query = (ctable.show_in_menu == True)
    configs = db(query).select(ctable.id,
                               ctable.name)
    for config in configs:
        if config.id == 1 or \
          (personal_config and config.id == personal_config.id):
            continue
        gis_menu.append(
            [{"name": config.name,
              "id": "region_id_%s" % config.id,
              "value": session.s3.gis_config_id == config.id,
              "request_type": "load"},
             False,
             URL(args=request.args,
                 vars={"_config":config.id})])
    s3.gis_menu = [deployment_settings.get_gis_menu(),
                   True, URL(c='gis',f='config')]
    s3.gis_menu.append(gis_menu)
    response.menu.insert(gis_index, s3.gis_menu)

# END =========================================================================

