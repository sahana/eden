# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """
        Custom Application Options Menu

        Define one function per controller with the controller prefix as
        function name and with "self" as its only argument (must be an
        instance method!), and let it return the controller menu
        definition as an instance of the layout (=an S3NavigationItem
        subclass, standard: M).

        In the standard layout, the main item in a controller menu does
        not have a label. If you want to re-use a menu for multiple
        controllers, do *not* define a controller setting (c="xxx") in
        the main item.
    """

    def __init__(self, name):
        """ Constructor """

        try:
            self.menu = getattr(self, name)()
        except:
            self.menu = None

    # -------------------------------------------------------------------------
    @staticmethod
    def inv():
        """ INV / Inventory """

        ADMIN = current.session.s3.system_roles.ADMIN

        current.s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        settings = current.deployment_settings
        use_adjust = lambda i: not settings.get_inv_direct_stock_edits()
        use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    M("Receive", c="inv", f="recv")(
                        M("New", m="create"),
                        M("Exiting", vars = {"a":1}),
                        M("Timeline", args="timeline"),
                    ),
                    M("Send", c="inv", f="send")( 
                        M("New", m="create"),
                        M("Exiting", vars = {"a":1}),
                        M("Sent Shipments", m="summary"),
                        M("Search Shipped Items", f="track_item"),
                        M("Timeline", args="timeline"),
                    ),
                    M("Stock", c="inv", f="inv_item", m="summary")(
                        M("Adjust Stock Levels", f="adj", check=use_adjust),
                        M("Kitting", f="kitting"),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Warehouses", c="inv", f="warehouse")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Requests", c="req", f="req")(
                        M("Create", m="create"),
                        M("Requested Items", f="req_item"),
                     ),
                    M("Commitments", c="req", f="commit", check=use_commit)(
                     ),
                    M("Reports", c="inv", f="inv_item")(
                        M("Stock Matrix", f="inv_item", m="report"),
                        M("Distribution Report", c="inv", f="track_item",
                          vars=dict(report="dist")),
                    ),
                    M("Administration", restrict=[ADMIN])(
                        M("Items", c="supply", f="item", m="summary"),
                        M("Catalogs", c="supply", f="catalog"),
                        M("Item Categories", c="supply", f="item_category",
                          restrict=[ADMIN]),
                        M("Suppliers", c="inv", f="supplier"),
                        M("Facilities", c="inv", f="facility"),
                        M("Facility Types", c="inv", f="facility_type",
                          restrict=[ADMIN]),
                        M("Warehouse Types", c="inv", f="warehouse_type",
                          restrict=[ADMIN]),
                    )
                )
