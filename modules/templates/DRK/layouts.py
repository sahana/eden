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
                    if item.opts.right:
                        classes.append("menu-right")
                else:
                    toplevel = False

                if item.components:
                    classes.append("has-dropdown not-click")
                    if item.selected:
                        classes.append("active")
                    _class = " ".join(classes)
                    # Menu item with Dropdown
                    if item.get_first(enabled=True):
                        _href = item.url()
                        return LI(A(item.label,
                                    _href=_href,
                                    _id=item.attr._id
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
                    if "menu-right" in item["_class"]:
                        item.remove_class("menu-right")
                        right.append(item)
                    else:
                        left.append(item)
                right.reverse()
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
                           SECTION(UL(right, _class="right"),
                                   UL(left, _class="left"),
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
class S3PersonalMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):

        if item.parent is None:
            # The menu
            items = item.render_components()
            if items:
                return TAG["ul"](items, _class="sub-nav personal-menu")
            else:
                return "" # menu is empty
        else:
            # A menu item
            if item.enabled and item.authorized:
                return TAG["li"](A(item.label, _href=item.url()))
            else:
                return None

# -----------------------------------------------------------------------------
# Shortcut
MP = S3PersonalMenuLayout

# =============================================================================
class S3AboutMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):

        if item.parent is None:
            # The menu
            items = item.render_components()
            if items:
                return TAG["ul"](items, _class="sub-nav about-menu left")
            else:
                return "" # menu is empty
        else:
            # A menu item
            if item.enabled and item.authorized:
                return TAG["li"](A(item.label, _href=item.url()))
            else:
                return None

# -----------------------------------------------------------------------------
# Shortcut
MA = S3AboutMenuLayout

# =============================================================================
class S3LanguageMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):
        """ Language menu layout

            options for each entry:
                - lang_code: the language code
                - lang_name: the language name
            option for the menu
                - current_language: code of the current language
        """

        if item.enabled:
            if item.components:
                # The language menu itself
                current_language = current.T.accepted_language
                items = item.render_components()
                select = SELECT(items, value=current_language,
                                    _name="_language",
                                    # @ToDo T:
                                    _title="Language Selection",
                                    _onchange="S3.reloadWithQueryStringVars({'_language':$(this).val()});")
                form = FORM(select, _class="language-selector",
                                    _name="_language",
                                    _action="",
                                    _method="get")
                return form
            else:
                # A language entry
                return OPTION(item.opts.lang_name,
                              _value=item.opts.lang_code)
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
ML = S3LanguageMenuLayout

# =============================================================================
class S3OrgMenuLayout(S3NavigationItem):
    """ Layout for the organisation-specific menu """

    @staticmethod
    def layout(item):

        name = "Deutsches Rotes Kreuz"
        logo = IMG(_src = "/%s/static/themes/DRK/img/logo_small.png" %
                          current.request.application,
                   _alt = "Deutsches Rotes Kreuz",
                   _width=40,
                   )

        # Note: render using current.menu.org.render()[0] + current.menu.org.render()[1]
        return (name, logo)

# -----------------------------------------------------------------------------
# Shortcut
OM = S3OrgMenuLayout

# END =========================================================================
