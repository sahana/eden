# -*- coding: utf-8 -*-

from gluon import A, DIV, LI, UL
from s3 import ICON, S3NavigationItem
from s3theme import NAV

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
            if item.parent is not None:
                if item.enabled and item.authorized:

                    attr = {"_id": item.attr._id}
                    if item.attr._onclick:
                        attr["_onclick"] = item.attr._onclick
                    else:
                        attr["_href"] = item.url()

                    if item.components:
                        # Submenu
                        items = item.render_components()

                        # Hide submenus which have no active links
                        if not items and not item.link:
                            return None

                        _class = ""
                        if item.parent.parent is None and item.selected:
                            _class = "active"

                        icon = item.opts.icon
                        if icon:
                            icon = ICON(icon)
                        else:
                            icon = ""

                        section = [LI(icon,
                                      A(item.label,
                                        **attr
                                        ),
                                      _class="heading %s" % _class,
                                      ),
                                   ]

                        if items:
                            section.append(UL(items))
                        return section

                    else:
                        # Submenu item
                        if item.parent.parent is None:
                            _class = "heading"
                        else:
                            _class = ""

                        icon = item.opts.icon
                        if icon:
                            icon = ICON(icon)
                        else:
                            icon = ""

                        return LI(A(icon,
                                    item.label,
                                    **attr
                                    ),
                                  _class=_class,
                                  )
            else:
                # Main menu
                items = item.render_components()
                return DIV(NAV(UL(items, _id="main-sub-menu", _class="side-nav")), _class="sidebar")

        else:
            return None

# END =========================================================================
