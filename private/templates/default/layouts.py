# -*- coding: utf-8 -*-

from gluon import *
from gluon.storage import Storage
from s3 import *

# Below is an example which you can base your own template's layout.py on
# - there are also other examples in the other templates folders
# - you will need to restart web2py after making changes to this file

# =============================================================================
#class S3MainMenuLayout(S3NavigationItem):
    #"""
        #Application Main Menu Layout

        #The layout() function takes an S3NavigationItem instance as input
        #and renders it as an HTML helper class instance. If the item can
        #or shall not be rendered on the page, this method must return None.

        #S3NavigationItem instances provide a number of attributes and methods
        #to support context-sensisitve rendering (see modules/s3/s3navigation.py).

        #Note that individual items can override the layout method by explicitly
        #setting the layout-property in the item's constructor.
    #"""

    #@staticmethod
    #def layout(item):
        #""" Custom Layout Method """

        ## Manage flags: hide any disabled/unauthorized items
        #if not item.authorized:
            #item.enabled = False
            #item.visible = False
        #elif item.enabled is None or item.enabled:
            #item.enabled = True
            #item.visible = True

        #if item.enabled and item.visible:

            #items = item.render_components()
            #if item.parent is not None:
                #if item.opts.right:
                    #_class = "fright"
                #else:
                    #_class = "fleft"
                #if item.components:
                    ## Submenu, render only if there's at list one active item
                    #if item.get_first(enabled=True):
                        #_href = item.url()
                        #return LI(DIV(A(item.label,
                                        #_href=_href,
                                        #_id=item.attr._id),
                                        #_class="hoverable"),
                                  #UL(items,
                                     #_class="submenu"),
                                  #_class=_class)
                #else:
                    ## Menu item
                    #if item.parent.parent is None:
                        ## Top-level item
                        #_href = item.url()
                        #if item.is_first():
                            ## 1st item, so display logo
                            #link = DIV(SPAN(A(_href=_href),
                                            #_class="S3menulogo"),
                                       #SPAN(A(item.label, _href=_href),
                                            #_class="S3menuHome"),
                                       #_class="hoverable")
                        #else:
                            #link = DIV(A(item.label,
                                         #_href=item.url(),
                                         #_id=item.attr._id),
                                       #_class="hoverable")
                        #return LI(link, _class=_class)
                    #else:
                        ## Submenu item
                        #if isinstance(item.label, dict):
                            #if "name" in item.label:
                                #label = item.label["name"]
                            #else:
                                #return None
                        #else:
                            #label = item.label
                        #link = A(label, _href=item.url(), _id=item.attr._id)
                        #return LI(link)
            #else:
                ## Main menu
                #return UL(items, _id="modulenav")

        #else:
            #return None

# END =========================================================================
