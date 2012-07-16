# -*- coding: utf-8 -*-

from gluon import *
from gluon.storage import Storage
from s3 import *

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
    """
        Application Main Menu Layout
    """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        # Manage flags: hide any disabled/unauthorized items
        if not item.authorized:
            item.enabled = False
            item.visible = False
        elif item.enabled is None or item.enabled:
            item.enabled = True
            item.visible = True

        if item.enabled and item.visible:

            items = item.render_components()
            if item.parent is not None:
                # Menu Item
                _class = item.selected and "selected" or ""
                if item.opts.right:
                    _class = "fright selected" if _class else "fright"
                else:
                    _class = "fleft selected" if _class else "fleft"
                _href = item.url()
                link = A(DIV(item.label,
                             _class="hoverable"),
                         _href=item.url(),
                         _id=item.attr._id)
                return LI(link, _class=_class)
            else:
                # Main menu
                return UL(items, _id="modulenav")

        else:
            return None

# =============================================================================
class S3TopMenuLayout(S3NavigationItem):
    """
        Top Menu Layout
    """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        if item.parent is None:
            # The menu
            items = item.render_components()
            if items:
                return UL(items)
            else:
                return "" # menu is empty
        else:
            # A menu item
            if item.enabled and item.authorized:
                return LI(A(DIV(item.label,
                                _class="hoverable"),
                            _href=item.url()),
                          _class="fleft")
            else:
                return None

# -----------------------------------------------------------------------------
# Shortcut
MT = S3TopMenuLayout

# END =========================================================================
