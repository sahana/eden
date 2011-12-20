# -*- coding: utf-8 -*-

""" S3 Situations

    @author: nursix

"""

prefix = "sit"

# -----------------------------------------------------------------------------
# Situation super-entity
situation_types = Storage(
    irs_incident = T("Incident"),
    rms_req = T("Request"),
    pr_presence = T("Presence")
)

tablename = "sit_situation"
table = super_entity(tablename, "sit_id", situation_types,
                     Field("datetime", "datetime"),
                     location_id(),
                     )

s3mgr.configure(tablename, editable=False, deletable=False, listadd=False)

# -----------------------------------------------------------------------------
# Trackable super-entity
# Use:
#       - add a field with super_link(db.sit_trackable)
#       - add as super-entity in configure (super_entity=db.sit_trackable)
#
trackable_types = Storage(
    asset_asset = T("Asset"),
    pr_person = T("Person"),
    dvi_body = T("Dead Body")
)

tablename = "sit_trackable"
table = super_entity(tablename, "track_id", trackable_types,
                     Field("track_timestmp", "datetime",
                           readable=False,
                           writable=False),
                     )

s3mgr.configure(tablename,
                editable=False,
                deletable=False,
                listadd=False)

# -----------------------------------------------------------------------------
# Universal presence
# Use:
#       - will be automatically available to all trackable types
#
tablename = "sit_presence"
table = db.define_table(tablename,
                        super_link(db.sit_trackable),
                        Field("timestmp", "datetime",
                              label=T("Date/Time")),
                        location_id(),
                        Field("interlock",
                              readable=False,
                              writable=False),
                        *s3_meta_fields())

# Shared component of all trackable types
s3mgr.model.add_component(table, sit_trackable=super_key(db.sit_trackable))

# -----------------------------------------------------------------------------

