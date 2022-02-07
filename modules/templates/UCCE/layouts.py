# -*- coding: utf-8 -*-

__all__ = ("S3OptionsMenuLayout",
           )

from gluon import current, A, LI, SPAN, UL
from s3 import ICON, S3NavigationItem
from s3theme import NAV

# =============================================================================
class S3OptionsMenuLayout(S3NavigationItem):
    """
        Controller Options Menu Layout
        - version with support for Icons
        - currently assumes all entries have icons
        - currently assumes no nested menus

        Classes use Foundation's Menu component
            https://get.foundation/sites/docs/menu.html
    """

    @staticmethod
    def layout(item):
        """ Layout Method (Item Renderer) """

        # Manage flags: hide any disabled/unauthorized items
        if not item.authorized:
            enabled = False
            visible = False
        elif item.enabled is None or item.enabled:
            enabled = True
            visible = True

        if enabled and visible:
            if item.parent is not None:
                if item.enabled and item.authorized:

                    attr = {"_id": item.attr._id}
                    if item.attr._onclick:
                        attr["_onclick"] = item.attr._onclick
                    else:
                        attr["_href"] = item.url()

                    #if item.components:
                    #    # Submenu
                    #    items = item.render_components()

                    #    # Hide submenus which have no active links
                    #    if not items and not item.link:
                    #        return None

                    #    _class = ""
                    #    if item.parent.parent is None and item.selected:
                    #        _class = "active"

                    #    section = [LI(A(ICON(item.opts.icon),
                    #                    " ",
                    #                    SPAN(item.label),
                    #                    **attr
                    #                    ),
                    #                  _class = "heading %s" % _class,
                    #                  ),
                    #               ]

                    #    if items:
                    #        section.append(UL(items,
                    #                          _class = "menu vertical nested", # https://get.foundation/sites/docs/menu.html
                    #                          ))
                    #    return section

                    #else:
                    # Submenu item
                    #if item.parent.parent is None:
                    #    _class = "heading"
                    if item.selected:
                        _class = "active"
                    else:
                        _class = ""

                    return LI(A(ICON(item.opts.icon),
                                " ",
                                SPAN(item.label),
                                **attr
                                ),
                              _class = _class,
                              )
            else:
                # Main menu
                items = item.render_components()
                return NAV(UL(items,
                              _id = "main-sub-menu",
                              _class = "menu vertical icons icon-top", # https://get.foundation/sites/docs/menu.html
                              ),
                           )

        else:
            return None

# END =========================================================================
