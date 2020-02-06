# -*- coding: utf-8 -*-

from gluon import current, A, DIV, FORM, OPTION, SELECT, TAG
from s3 import ICON, S3NavigationItem
#from s3theme import NAV

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
                select = SELECT(items,
                                value = current_language,
                                _name = "_language",
                                # @ToDo T:
                                _title = "Language Selection",
                                _onchange = "S3.reloadWithQueryStringVars({'_language':$(this).val()});",
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
                              _value = item.opts.lang_code,
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
ML = S3LanguageMenuLayout

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
