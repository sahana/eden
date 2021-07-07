# -*- coding: utf-8 -*-

from gluon import *
#from gluon.storage import Storage
from s3 import *
#from s3theme import NAV, SECTION

# =============================================================================
class CIRCLE(DIV):
    """ <circle> element """

    tag = "circle"

# =============================================================================
class PATH(DIV):
    """ <path> element """

    tag = "path"

# =============================================================================
class SVG(DIV):
    """ <svg> element """

    tag = "svg"

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
    """ Custom Main Menu Layout """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        T = current.T

        divs = [DIV(DIV(A(SVG(PATH(_d = "M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z",
                                   ),
                              _fill = "#5f6368",
                              ),
                          _href = "#",
                          _class = "ha",
                          _role = "button",
                          _title = T("Main menu"),
                          ),
                        _class = "hd",
                        ),
                    _class = "large-2 medium-3 small-4 columns",
                    ),
                DIV(_class = "large-8 medium-6 small-4 columns",
                    ),
                DIV(DIV(A(SVG(PATH(_fill = "none",
                                   _d = "M0 0h24v24H0z",
                                   ),
                              PATH(_d = "M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z",
                                   ),
                              _fill = "#5f6368",
                              ),
                          _href = URL(c = "default",
                                      f = "help",
                                      ),
                          _class = "ha",
                          _role = "button",
                          _title = T("Support"),
                          ),
                        _class = "hd",
                        ),
                    DIV(A(SVG(PATH(_d = "M13.85 22.25h-3.7c-.74 0-1.36-.54-1.45-1.27l-.27-1.89c-.27-.14-.53-.29-.79-.46l-1.8.72c-.7.26-1.47-.03-1.81-.65L2.2 15.53c-.35-.66-.2-1.44.36-1.88l1.53-1.19c-.01-.15-.02-.3-.02-.46 0-.15.01-.31.02-.46l-1.52-1.19c-.59-.45-.74-1.26-.37-1.88l1.85-3.19c.34-.62 1.11-.9 1.79-.63l1.81.73c.26-.17.52-.32.78-.46l.27-1.91c.09-.7.71-1.25 1.44-1.25h3.7c.74 0 1.36.54 1.45 1.27l.27 1.89c.27.14.53.29.79.46l1.8-.72c.71-.26 1.48.03 1.82.65l1.84 3.18c.36.66.2 1.44-.36 1.88l-1.52 1.19c.01.15.02.3.02.46s-.01.31-.02.46l1.52 1.19c.56.45.72 1.23.37 1.86l-1.86 3.22c-.34.62-1.11.9-1.8.63l-1.8-.72c-.26.17-.52.32-.78.46l-.27 1.91c-.1.68-.72 1.22-1.46 1.22zm-3.23-2h2.76l.37-2.55.53-.22c.44-.18.88-.44 1.34-.78l.45-.34 2.38.96 1.38-2.4-2.03-1.58.07-.56c.03-.26.06-.51.06-.78s-.03-.53-.06-.78l-.07-.56 2.03-1.58-1.39-2.4-2.39.96-.45-.35c-.42-.32-.87-.58-1.33-.77l-.52-.22-.37-2.55h-2.76l-.37 2.55-.53.21c-.44.19-.88.44-1.34.79l-.45.33-2.38-.95-1.39 2.39 2.03 1.58-.07.56a7 7 0 0 0-.06.79c0 .26.02.53.06.78l.07.56-2.03 1.58 1.38 2.4 2.39-.96.45.35c.43.33.86.58 1.33.77l.53.22.38 2.55z",
                                   ),
                              CIRCLE(_cx = "12",
                                     _cy = "12",
                                     _r = "3.5",
                                     ),
                              _fill = "#5f6368",
                              ),
                          _href = "#",
                          _class = "ha",
                          _role = "button",
                          _title = T("Settings"),
                          ),
                        _class = "hd",
                        ),
                    DIV(A(SVG(PATH(_d = "M6,8c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM12,20c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM6,20c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM6,14c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM12,14c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM16,6c0,1.1 0.9,2 2,2s2,-0.9 2,-2 -0.9,-2 -2,-2 -2,0.9 -2,2zM12,8c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM18,14c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM18,20c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2z",
                                   ),
                              _fill = "#5f6368",
                              ),
                          _href = "#",
                          _class = "ha",
                          _role = "button",
                          _title = T("RMS modules"),
                          ),
                        _class = "hd",
                        ),
                    DIV(A(s3_avatar_represent(current.auth.user.id,
                                              _class = "ip",
                                              _height = 36,
                                              _width = 36,
                                              ),
                          _href = "#",
                          _class = "hap",
                          _role = "button",
                          _title = T("RMS Account"),
                          ),
                        _class = "hdp",
                        ),
                    _class = "large-2 medium-3 small-4 columns",
                    ),
                ]

        return TAG[""](*divs)

# =============================================================================
def auth_formstyle(form, fields, *args, **kwargs):
    """
        Formstyle for the Login box on the homepage
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        if hasattr(widget, "element"):
            submit = widget.element("input", _type="submit")
            if submit:
                submit.add_class("small primary button")
            elif label:
                widget["_placeholder"] = label[0]

        return DIV(widget,
                   _class = "medium-3 columns",
                   _id = row_id,
                   )

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# -----------------------------------------------------------------------------
class S3LoginMenuLayout(S3NavigationItem):
    """ Layout for the Login box in top navigation """

    @staticmethod
    def layout(item):

        auth = current.auth
        auth.settings.label_separator = ""
        formstyle = auth_formstyle
        login_form = auth.login(formstyle = formstyle)

        return login_form

# -----------------------------------------------------------------------------
# Shortcut
LM = S3LoginMenuLayout

# =============================================================================
class S3AboutMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):

        if item.parent is None:
            # The menu
            items = item.render_components()
            if items:
                return UL(items, _class="sub-nav about-menu left")
            else:
                return "" # menu is empty
        else:
            # A menu item
            if item.enabled and item.authorized:
                return LI(A(item.label, _href=item.url()))
            else:
                return None

# -----------------------------------------------------------------------------
# Shortcut
MA = S3AboutMenuLayout

# =============================================================================
class S3OrgMenuLayout(S3NavigationItem):
    """ Layout for the organisation-specific menu """

    @staticmethod
    def layout(item):
        """
            @ToDo: Migrate to s3db.org_logo_represent
        """

        name = "IFRC"
        logo = None

        # Lookup Root Organisation name & Logo
        root_org = current.auth.root_org()
        if root_org:
            db = current.db
            s3db = current.s3db
            language = current.session.s3.language
            if language == current.deployment_settings.get_L10n_default_language():
                l10n = None
            else:
                ltable = s3db.org_organisation_name
                query = (ltable.organisation_id == root_org) & \
                        (ltable.language == language)
                l10n = db(query).select(ltable.name_l10n,
                                        ltable.acronym_l10n,
                                        limitby = (0, 1),
                                        cache = s3db.cache,
                                        ).first()
            table = s3db.org_organisation
            record = db(table.id == root_org).select(table.name,
                                                     #table.acronym,
                                                     table.logo,
                                                     limitby = (0, 1),
                                                     cache = s3db.cache,
                                                     ).first()
            if l10n:
                #if l10n.acronym_l10n:
                    #name = _name = l10n.acronym_l10n
                #else:
                name = l10n.name_l10n

            if record:
                if not l10n:
                    #if record.acronym:
                        #name = _name = record.acronym
                    #else:
                    name = record.name

                if record.logo:
                    size = (60, None)
                    image = s3db.pr_image_library_represent(record.logo, size=size)
                    url_small = URL(c="default", f="download", args=image)
                    alt = "%s logo" % name
                    logo = IMG(_src=url_small, _alt=alt, _width=60)

        if not logo:
            # Default to generic IFRC
            logo = IMG(_src = "/%s/static/themes/RMSAmericas/img/logo_small.png" %
                              current.request.application,
                       _alt = current.T("Red Cross/Red Crescent"),
                       _width = 60,
                       )

        # Note: render using current.menu.org.render()[0] + current.menu.org.render()[1]
        #return (name, logo)
        return logo

# -----------------------------------------------------------------------------
# Shortcut
OM = S3OrgMenuLayout

# END =========================================================================
