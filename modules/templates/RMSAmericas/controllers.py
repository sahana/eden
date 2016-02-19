# -*- coding: utf-8 -*-

from os import path

from gluon import *

from s3 import S3CustomController

THEME = "RMSAmericas"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        if current.deployment_settings.has_module("cms"):
            system_roles = current.auth.get_system_roles()
            ADMIN = system_roles.ADMIN in current.session.s3.roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            item = current.db(query).select(table.body,
                                            table.id,
                                            limitby=(0, 1)).first()
            if item:
                if ADMIN:
                    item = DIV(XML(item.body),
                               BR(),
                               A(current.T("Edit"),
                                 _href=URL(c="cms", f="post",
                                           args=[item.id, "update"]),
                                 _class="action-btn"))
                else:
                    item = DIV(XML(item.body))
            elif ADMIN:
                if current.response.s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = A(current.T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module": module,
                                         "resource": resource
                                         }),
                         _class="%s cms-edit" % _class)
            else:
                item = ""
        else:
            item = ""
        output["item"] = item

        self._view(THEME, "index.html")
        return output

# =============================================================================
def deploy_index():
    """
        Custom module homepage for deploy (=RIT) to display online
        documentation for the module
    """

    response = current.response

    def prep(r):
        default_url = URL(f="mission", args="summary", vars={})
        return current.s3db.cms_documentation(r, "RIT", default_url)
    response.s3.prep = prep
    output = current.rest_controller("cms", "post")

    # Custom view
    view = path.join(current.request.folder,
                     "modules",
                     "templates",
                     THEME,
                     "views",
                     "deploy",
                     "index.html",
                     )
    try:
        # Pass view as file not str to work in compiled mode
        response.view = open(view, "rb")
    except IOError:
        from gluon.http import HTTP
        raise HTTP(404, "Unable to open Custom View: %s" % view)

    return output

# END =========================================================================
