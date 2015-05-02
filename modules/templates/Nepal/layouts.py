# -*- coding: utf-8 -*-

from gluon import *
from s3 import *

# =============================================================================
class IndexMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):
        """ Layout Method (Item Renderer) """

        # Manage flags: hide any disabled/unauthorized items
        #if not item.authorized:
        #    enabled = False
        #    visible = False
        #elif item.enabled is None or item.enabled:
        #    enabled = True
        #    visible = True

        #if enabled and visible:
        if item.parent is None:
            # Return Menu
            items = item.render_components()
            return UL(items, _id="index-menu",
                      _class="small-block-grid-1 medium-block-grid-2 large-block-grid-4")
        else:
            if item.enabled:# and item.authorized:
                attr = dict(_id = item.attr._id,
                            _href = item.url())

                if item.components:
                    # Menu Icon
                    section = [A(H2(ICON(item.opts.get("icon",item.function)),
                                    BR(),
                                    item.label),
                                  **attr),
                               ]
                    items = item.render_components()
                    if items:
                        section.append(DIV(items))
                    section.append(P(item.opts.description))
                    return LI(section)
                else:
                    # Menu Icon Buttons
                    return A(ICON(item.opts.icon),
                             " ",
                             item.label,
                             _class="button small secondary",
                             **attr)
# END =========================================================================
