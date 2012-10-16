__all__ = ["w_autocomplete",
           "w_inv_item_select",
           "w_supply_select",
           "w_facility_select",
           "w_gis_location",
           ]

# @todo There are performance issues need to profile and find out in which functions are the bottlenecks

import time

from gluon import current

# -----------------------------------------------------------------------------
def _autocomple_finish(el_id, browser):
    giveup = 0.0
    sleeptime = 0.2
    el = browser.find_element_by_id(el_id)
    while giveup < 60:
        try:
            if el.find_elements_by_tag_name("option")[0].text != "":
                return
        except: # StaleElementReferenceException
            print "StaleElementReferenceException %s" % giveup
            el = browser.find_element_by_id(el_id)
        # The pack drop down hasn't been populated yet so sleep
        time.sleep(sleeptime)
        giveup += sleeptime

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
    giveup = 0.0
    sleeptime = 0.2
    while browser.find_element_by_id(throbber_id).is_displayed():
        time.sleep(sleeptime)
        giveup += sleeptime
        if giveup > 60:
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
                    time.sleep(15)
                    # The id is copied into the value attribute so use that
                    return int(db_id.get_attribute("value"))
                autoitem += 1
            automenu += 1
            try:
                menu = browser.find_element_by_id("ui-menu-%s" % automenu)
            except:
                menu = None
            # end of looping through each autocomplete menu
        time.sleep(sleeptime)

# -----------------------------------------------------------------------------
def w_inv_item_select (item_repr,
                       tablename,
                       field,
                       quiet = True,
                      ):
    config = current.test_config
    browser = config.browser

    el_id = "%s_%s" % (tablename, field)
    el = browser.find_element_by_id(el_id)
    raw_value = None
    for option in el.find_elements_by_tag_name("option"):
        if option.text == item_repr:
            option.click()
            raw_value = int(option.get_attribute("value"))
            break
    # Now wait for the pack_item to be populated
    el_id = "%s_%s" % (tablename, "item_pack_id")
    _autocomple_finish(el_id, browser)
    return raw_value

# -----------------------------------------------------------------------------
def w_supply_select(item_repr,
                    tablename,
                    field,
                    quiet = True,
                   ):
    el_id = "%s_%s" % (tablename, field)
    raw_value = w_autocomplete(item_repr, el_id)
    # Now wait for the pack_item to be populated
    browser = current.test_config.browser
    el_id = "%s_%s" % (tablename, "item_pack_id")
    _autocomple_finish(el_id, browser)
    return raw_value

# -----------------------------------------------------------------------------
def w_facility_select(item_repr,
                      tablename,
                      field,
                      quiet = True,
                     ):
    el_id = "%s_%s" % (tablename, field)
    raw_value = w_autocomplete(item_repr, el_id)
    # Now wait for the pack_item to be populated
    browser = current.test_config.browser
    el_id = "%s_%s" % (tablename, "site_id")
    _autocomple_finish(el_id, browser)
    return raw_value

# -----------------------------------------------------------------------------
def w_gis_location (item_repr,
                    field,
                    quiet = True,
                   ):
    config = current.test_config
    browser = config.browser

    if field == "L0":
        el_id = "gis_location_%s" % field
        el = browser.find_element_by_id(el_id)
        for option in el.find_elements_by_tag_name("option"):
            if option.text == item_repr:
                option.click()
                raw_value = int(option.get_attribute("value"))
                break
    elif field[0] == "L":
        # @todo make this a proper autocomplete widget (select or add)
        el_id = "gis_location_%s_ac" % field
        el = browser.find_element_by_id(el_id)
        el.send_keys(item_repr)
        raw_value = None # can't get the id at the moment (see the todo)
    else:
        el_id = "gis_location_%s" % field
        el = browser.find_element_by_id(el_id)
        el.send_keys(item_repr)
        raw_value = item_repr
    return raw_value

# END =========================================================================
