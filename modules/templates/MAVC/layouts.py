# -*- coding: utf-8 -*-

from gluon import *
from gluon.storage import Storage
from s3 import *
from s3theme import NAV, SECTION

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
    """ Custom Main Menu Layout """

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

                classes = []

                if item.parent.parent is None:
                    # Item at the top-level?
                    toplevel = True
                    if item.opts.left:
                        classes.append("menu-left")
                    #if item.opts.right:
                    #    classes.append("menu-right")
                else:
                    toplevel = False

                if item.components:
                    classes.append("has-dropdown not-click")
                    if item.selected:
                        classes.append("active")
                    if item.opts.icon:
                        classes.append("label-icon")
                        title = item.label
                        item.label = ICON(item.opts.icon)
                    else:
                        title = None
                    _class = " ".join(classes)

                    # Menu item with Dropdown
                    if item.get_first(enabled=True):
                        _href = item.url()
                        return LI(A(item.label,
                                    _href = _href,
                                    _id = item.attr._id,
                                    _title = title,
                                    ),
                                  UL(items,
                                     _class="dropdown"
                                     ),
                                  _class=_class,
                                  )
                else:
                    # Menu item without Drop-Down
                    if toplevel:
                        item_url = item.url()
                        if item_url == URL(c="default", f="index"):
                            classes.append("menu-home")
                        if item.selected:
                            classes.append("active")
                        _class = " ".join(classes)
                        return LI(A(item.label,
                                    _href=item_url,
                                    _id=item.attr._id,
                                    ),
                                  _class=_class,
                                  )
                    else:
                        # Submenu item
                        if isinstance(item.label, dict):
                            if "name" in item.label:
                                label = item.label["name"]
                            else:
                                return None
                        else:
                            label = item.label
                        link = A(label, _href=item.url(), _id=item.attr._id)
                        return LI(link)
            else:
                # Main menu

                right = []
                left = []
                for item in items:
                    if "menu-left" in item["_class"]:
                        item.remove_class("menu-left")
                        left.append(item)
                    else:
                        right.append(item)
                #right.reverse()
                if current.response.s3.rtl:
                    right, left = left, right
                return NAV(UL(LI(A(" ",
                                   _href=URL(c="default", f="index"),
                                   ),
                                 _class="name"
                                 ),
                              LI(A(SPAN(current.T("Menu"))),
                                 _class="toggle-topbar menu-icon",
                                 ),
                              _class="title-area",
                              ),
                           SECTION(UL(left, _class="left"),
                                   UL(right, _class="right"),
                                   _class="top-bar-section",
                                   ),
                           _class = "top-bar",
                           data = {"topbar": " "},
                           )
        else:
            return None

    # ---------------------------------------------------------------------
    @staticmethod
    def checkbox_item(item):
        """ Render special active items """

        name = item.label
        link = item.url()
        _id = name["id"]
        if "name" in name:
            _name = name["name"]
        else:
            _name = ""
        if "value" in name:
            _value = name["value"]
        else:
            _value = False
        if "request_type" in name:
            _request_type = name["request_type"]
        else:
            _request_type = "ajax"
        if link:
            if _request_type == "ajax":
                _onchange='''var val=$('#%s:checked').length;$.getS3('%s'+'?val='+val,null,false,null,false,false)''' % \
                             (_id, link)
            else:
                # Just load the page. Use this if the changed menu
                # item should alter the contents of the page, and
                # it's simpler just to load it.
                _onchange="location.href='%s'" % link
        else:
            _onchange=None
        return LI(A(INPUT(_type="checkbox",
                          _id=_id,
                          _onchange=_onchange,
                          value=_value,
                          ),
                    "%s" % _name,
                    _nowrap="nowrap",
                    ),
                  _class="menu-toggle",
                  )

# =============================================================================
class S3FooterMenuLayout(S3NavigationItem):
    """ MAVC Footer Menu Layout """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        if not item.authorized:
            item.enabled = item.visible = False
        elif item.enabled is None or item.enabled:
            item.enabled = item.visible = True

        if item.enabled and item.visible:

            if item.parent is not None:

                return LI(A(item.label,
                            _href = item.url(),
                            _id = item.attr._id,
                            _class = "footer-menu-item",
                            ))

            else:
                # The menu itself
                items = item.render_components()

                # Homepage link
                logo = "/%s/static/themes/MAVC/img/footer-logo.png" % \
                       current.request.application

                return TAG[""](UL(items,
                                  _class = "footer-menu",
                                  ),
                               A(IMG(_src=logo),
                                 _href = URL("default", "index"),
                                 _class = "footer-home",
                                 ),
                               )
        else:
            return None

# -----------------------------------------------------------------------------
# Shortcut
#
MF = S3FooterMenuLayout

# =============================================================================
class S3LanguageMenuLayout(S3NavigationItem):
    """ Custom Language Menu (Dropdown) """

    @staticmethod
    def layout(item):
        """
            Language menu layout

            options for each entry:
                - lang_code: the language code
                - lang_name: the language name
        """

        if item.enabled:
            if item.components:
                # The language menu itself
                T = current.T
                items = item.render_components()
                select = SELECT(items,
                                _name = "_language",
                                _title = T("Language Selection"),
                                _onchange = '''S3.reloadWithQueryStringVars({'_language':$(this).val()})''',
                                value = T.accepted_language,
                                )
                form = FORM(select,
                            _class = "language-selector",
                            _name = "_language",
                            _action = "",
                            _method = "get",
                            )
                return form
            else:
                # A language entry
                return OPTION(item.opts.lang_name,
                              _value=item.opts.lang_code,
                              )
        else:
            return None

    # -------------------------------------------------------------------------
    def check_enabled(self):
       """ Check whether the language menu is enabled """

       if current.deployment_settings.get_L10n_display_toolbar():
           return True
       else:
           return False

# -----------------------------------------------------------------------------
# Shortcut
#
ML = S3LanguageMenuLayout

# END =========================================================================
