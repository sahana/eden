# -*- coding: utf-8 -*-

from gluon import A, DIV, TAG
from s3 import ICON, S3NavigationItem
#from s3theme import NAV

# =============================================================================
class S3OptionsMenuLayout(S3NavigationItem):
    """
        Side Menu Layout
    """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        # Manage flags: hide any disabled/unauthorized items
        if not item.authorized:
            enabled = False
            visible = False
        elif item.enabled is None or item.enabled:
            enabled = True
            visible = True

        if enabled and visible:
            if item.parent is None:
                # Main menu
                items = item.render_components()
                return DIV(items, _id="main-sub-menu", _class="icon-bar vertical three-up")

            else:   
                # Menu item
                if item.enabled and item.authorized:

                    attr = {"_id": item.attr._id}
                    if item.attr._onclick:
                        attr["_onclick"] = item.attr._onclick
                    else:
                        attr["_href"] = item.url()

                    if item.selected:
                        attr["_class"] = "active item"
                    else:
                        attr["_class"] = "item"

                    icon = item.opts.icon
                    if icon:
                        icon = ICON(icon)
                    else:
                        icon = ""

                    return A(icon,
                             TAG["label"](item.label),
                             **attr
                             )
        else:
            return None

# END =========================================================================
