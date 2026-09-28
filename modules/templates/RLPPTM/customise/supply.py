"""
    SUPPLY module customisations for RLPPTM

    License: MIT
"""

from gluon import current, IS_NOT_EMPTY

from core import ICON, S3Represent, s3_str

# -------------------------------------------------------------------------
def supply_item_resource(r, tablename):

    T = current.T
    s3db = current.s3db

    table = s3db.supply_item

    unused = (#"item_category_id",
              "brand_id",
              "kit",
              "model",
              "year",
              )
    for fn in unused:
        field = table[fn]
        field.readable = field.writable = False

    # Code is required
    field = table.code
    field.requires = [IS_NOT_EMPTY(), field.requires]

    # Represent categories by name (no hierarchy)
    field = table.item_category_id
    field.comment = None
    field.represent = S3Represent(lookup="supply_item_category")

    # Use a localized default for um
    field = table.um
    field.default = s3_str(T("piece"))

    # Expose obsolete-flag
    field = table.obsolete
    field.label = T("Not orderable")
    field.readable = field.writable = True
    field.represent = lambda v, row=None: ICON("remove") if v else ""

    # Filter widgets
    from core import TextFilter
    filter_widgets = [TextFilter(["name",
                                  "code",
                                  "comments",
                                  ],
                                 label = T("Search"),
                                 ),
                      ]
    s3db.configure("supply_item",
                   filter_widgets = filter_widgets,
                   )

# -------------------------------------------------------------------------
def supply_item_controller(**attr):

    s3db = current.s3db

    s3db.add_components("supply_item",
                        inv_track_item = "item_id",
                        )

    from ..rheaders import rlpptm_supply_rheader
    attr["rheader"] = rlpptm_supply_rheader

    return attr

# -------------------------------------------------------------------------
def shipping_code(prefix, site_id, field):

    # We hide the send_ref from the user, but still auto-generate one
    #if prefix == "WB":
    #    # Do not generate waybill numbers, but ask them from the user
    #    return None

    db = current.db
    if site_id:
        code = "%s-%s-" % (prefix, site_id)
    else:
        code = "%s-#-" % prefix

    number = 0
    if field:
        query = (field.like("%s%%" % code))
        ref_row = db(query).select(field,
                                   limitby = (0, 1),
                                   orderby = ~field
                                   ).first()
        if ref_row:
            ref = ref_row[field]
            try:
                number = int(ref[-6:])
            except (ValueError, TypeError):
                pass

    return "%s%06d" % (code, number + 1)

# END =========================================================================
