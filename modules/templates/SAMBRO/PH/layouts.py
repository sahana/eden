# -*- coding: utf-8 -*-

from gluon import *
from gluon.storage import Storage
from s3 import *
from s3theme import NAV, SECTION
from s3layouts import S3MainMenuDefaultLayout

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
   """
       Custom Main Menu Layout
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
                   _class = " ".join(classes)
                   # Menu item with Dropdown
                   if item.get_first(enabled=True):
                       _href = item.url()
                       return LI(A(SPAN(item.label),
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
                       return LI(A(SPAN(item.label),
                                   _href=item_url,
                                   _id=item.attr._id,
                                   ),
                                 _class=_class,
                                 )
                   else:
                       # Submenu item
                       if isinstance(item.label, dict):
                           if "id" in item.label:
                               return S3MainMenuDefaultLayout.checkbox_item(item)
                           elif "name" in item.label:
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

               T = current.T
               settings = current.deployment_settings
               logo_url = URL(c = "static",
                              f = "themes",
                              args = ["SAMBRO", "PH", "img", "pagasa.png"],
                              )
               home_url = URL(c = "default",
                              f = "index",
                              args = ["alert_hub_cop"]
                              )
               title_area = UL(LI(H1(A(IMG(_src = logo_url,
                                           _class = "logo",
                                           _alt = settings.get_system_name_short(),
                                           ),
                                       _href = home_url,
                                       ),
                                     ),
                                  _class = "name",
                                  ),
                               LI(A(SPAN(T("Menu"),
                                         ),
                                    _href = "#",
                                    ),
                                  _class = "toggle-topbar menu-icon",
                                  ),
                               _class = "title-area",
                               )

               return NAV(title_area,
                          SECTION(UL(right,
                                     _class = "right",
                                     ),
                                  UL(left,
                                     _class = "left",
                                     ),
                                  _class = "top-bar-section",
                                  ),
                          data = {"topbar": " "},
                          _class = "top-bar",
                          _role = "navigation",
                          )

       else:
           return None

# END =========================================================================
