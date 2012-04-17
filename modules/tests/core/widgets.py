__all__ = ["w_autocomplete",
          ]

# @todo Their are performance issues need to profile and find out in which functions are the bottlenecks
 
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys

from gluon import current

from s3 import s3_debug

import time

# -----------------------------------------------------------------------------
def w_autocomplete(search,
                 autocomplete,
                 needle = None,
                 quiet = True,
                ):
    """ helper function to find a search string in an autocomplete """
    import time 
    config = current.test_config
    browser = config.browser

    autocomplete_id = "dummy_%s_id" % autocomplete
    throbber_id = "dummy_%s_id_throbber" % autocomplete
    if needle == None:
        needle = search

    elem = browser.find_element_by_id(autocomplete_id)
    elem.clear()
    elem.send_keys(search)
    # We will wait for up-to a minute for the data to arrive
    # But try every second
    for i in range(10):
        # For each autocomplete on the form the menu will have an id starting from 0
        automenu = 0
        try:
            menu = browser.find_element_by_id("ui-menu-%s" % automenu)
        except:
            menu = None
        while menu:
            # for each item in the menu it will have an id starting from 0
            autoitem = 0
            if not quiet:
                print "Looking for element ui-menu-%s-%s" %(automenu,automenu)
            try:
                menuitem = browser.find_element_by_id("ui-menu-%s-%s" % (automenu,automenu))
            except:
                menuitem = None
            while menuitem:
                linkText = menuitem.text
                if not quiet:
                    print "Looking for %s found %s" %(needle, linkText)
                if needle in linkText:
                    # found the text need to click on it to get the db id
                    menuitem.click()
                    # wait for throbber to close
                    time.sleep(1)
                    giveup = 0
                    while browser.find_element_by_id(throbber_id).is_displayed:
                        time.sleep(1)
                        giveup += 1
                        if giveup == 20:
                            return
                    # throbber has closed and data was found, return
                    return
                autoitem += 1
                try:
                    menuitem = browser.find_element_by_id("%s-%s" % (menu,automenu))
                except:
                    menuitem = None
            # end of looping through each menu item
            automenu += 1
            try:
                menu = browser.find_element_by_id("ui-menu-%s" % automenu)
            except:
                menu = None
            # end of looping through each autocomplete menu
        time.sleep(1)
