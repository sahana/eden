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
    config = current.test_config
    browser = config.browser

    autocomplete_id = "dummy_%s" % autocomplete
    throbber_id = "dummy_%s_throbber" % autocomplete
    if needle == None:
        needle = search

    elem = browser.find_element_by_id(autocomplete_id)
    elem.clear()
    elem.send_keys(search)
    # give time for the throbber to appear
    time.sleep(1)
    # now wait for throbber to close
    giveup = 0
    while browser.find_element_by_id(throbber_id).is_displayed():
        time.sleep(1)
        giveup += 1
        if giveup == 20:
            return False
    # throbber has closed and data was found, return
    for i in range(10):
        # For each autocomplete on the form the menu will have an id starting from 0
        automenu = 0
        try:
            menu = browser.find_element_by_id("ui-menu-%s" % automenu)
        except:
            menu = None
        while menu:
            # Try and get the value directly
            menu_items = menu.text.splitlines()
            autoitem = 0
            for linkText in menu_items:
                if needle in linkText:
                    # found the text need to click on it to get the db id
                    menuitem = browser.find_element_by_id("ui-menu-%s-%s" % (automenu,autoitem))
                    menuitem.click()
                    db_id = browser.find_element_by_id(autocomplete)
                    # The id is copied into the value attribute so use that
                    return int(db_id.get_attribute("value"))
                autoitem += 1
            automenu += 1
            try:
                menu = browser.find_element_by_id("ui-menu-%s" % automenu)
            except:
                print "Unable to find another ui_menu"
                menu = None
            # end of looping through each autocomplete menu
        print "Sleeping"
        time.sleep(1)
