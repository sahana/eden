__all__ = ["dt_filter",
           "dt_row_cnt",
           "dt_data",
           "dt_data_item",
           "dt_find",
           "dt_links",
           "dt_action",
          ]

# @ToDo: There are performance issues
#        - need to profile and find out in which functions are the bottlenecks

import time

from gluon import current

# -----------------------------------------------------------------------------
def convert_repr_number (number):
    """
        Helper function to convert a string representation back to a number.
        Assumptions:
         * It may have a thousand separator
         * It may have a decimal point
         * If it has a thousand separator then it will have a decimal point
        It will return false is the number doesn't look valid
    """

    sep = ""
    dec = ""
    part_one = "0"
    part_two = ""
    for digit in number:
        if digit.isdigit():
            if sep == "":
                part_one += digit
            else:
                part_two += digit
        else:
            if digit == "-" and part_one == "0":
                part_one = "-0"
            elif sep == "" and sep != digit:
                sep = digit
            elif dec == "":
                dec = digit
                part_two += "."
            else:
                # Doesn't look like a valid number repr so return 
                return False
    if dec == "":
        return float("%s.%s" % (part_one, part_two))
    else:
        return float("%s%s" % (part_one, part_two))

# -----------------------------------------------------------------------------
def dt_filter(reporter,
              search_string=" ",
              forceClear = True,
              quiet = True):
    """
        Filter the dataTable
    """

    if forceClear:
        if not dt_filter(reporter,
                         forceClear = False,
                         quiet = quiet):
            return False
    config = current.test_config
    browser = config.browser

    sleep_limit = 10
    elem = browser.find_element_by_css_selector('label > input[type="text"]')
    elem.clear()
    elem.send_keys(search_string)

    time.sleep(1) # give time for the list_processing element to appear
    waiting_elem = browser.find_element_by_id("list_processing")
    sleep_time = 0
    while (waiting_elem.value_of_css_property("visibility") == "visible"):
        time.sleep(1)
        sleep_time += 1
        if sleep_time > sleep_limit:
            if not quiet:
                reporter("DataTable filter didn't respond within %d seconds" % sleep_limit)
            return False
    return True

# -----------------------------------------------------------------------------
def dt_row_cnt(reporter,
               check = (),
               quiet = True,
               utObj = None):
    """
        return the rows that are being displayed and the total rows in the dataTable
    """

    config = current.test_config
    browser = config.browser

    elem = browser.find_element_by_id("list_info")
    details = elem.text
    if not quiet:
        reporter(details)
    words = details.split()
    start = int(words[1])
    end = int(words[3])
    length = int(words[5])
    filtered = None
    if len(words) > 10:
        filtered = int(words[9])
    if check != ():
        if len(check ) == 3:
            expected = "Showing %d to %d of %d entries" % check
            actual = "Showing %d to %d of %d entries" % (start, end, length)
            msg = "Expected result of '%s' doesn't equal '%s'" % (expected, actual)
            if utObj != None:
                utObj.assertEqual((start, end, length) == check, msg)
            else:
                assert (start, end, length) == check, msg
        elif len(check) == 4:
            expected = "Showing %d to %d of %d entries (filtered from %d total entries)" % check
            if filtered:
                actual = "Showing %d to %d of %d entries (filtered from %d total entries)" % (start, end, length, filtered)
            else:
                actual = "Showing %d to %d of %d entries" % (start, end, length)
            msg = "Expected result of '%s' doesn't equal '%s'" % (expected, actual)
            if utObj != None:
                utObj.assertEqual((start, end, length) == check, msg)
            else:
                assert (start, end, length, filtered) == check, msg
    if len(words) > 10:
        return (start, end, length, filtered)
    else:
        return (start, end, length)

# -----------------------------------------------------------------------------
def dt_data(row_list = None,
            add_header = False):
    """ return the data in the displayed dataTable """

    config = current.test_config
    browser = config.browser

    cell = browser.find_element_by_id("table-container")
    text = cell.text
    parts = text.splitlines()
    records = []
    cnt = 0
    lastrow = ""
    header = ""
    for row in parts:
        if row.startswith("Detail"):
            header = lastrow
            row = row[8:]
            if row_list == None or cnt in row_list:
                records.append(row)
            cnt += 1
        else:
            lastrow = row
    if add_header:
        return [header] + records
    return records

# -----------------------------------------------------------------------------
def dt_data_item(row = 1,
                 column = 1,
                 tableID = "list",
                ):
    """ Returns the data found in the cell of the dataTable """

    config = current.test_config
    browser = config.browser

    td =  ".//*[@id='%s']/tbody/tr[%s]/td[%s]" % (tableID, row, column)
    try:
        elem = browser.find_element_by_xpath(td)
        return elem.text
    except:
        return False

# -----------------------------------------------------------------------------
def dt_find(search = "",
            row = None,
            column = None,
            cellList = None,
            tableID = "list",
            first = False,
           ):
    """
        Find the cells where search is found in the dataTable
        search: the string to search for. If you pass in a number (int, float)
                then the function will attempt to convert all text values to
                a float for comparison by using the convert_repr_number helper
                function
        row: The row or list of rows to search along
        column: The column or list of columns to search down
        cellList: This is a list of cells which may be returned from a previous
                  call, these cells will be searched again for the search string.
                  However if a row or column value is also provided then for
                  each cell in cellList the column or row will be offset.
                  For example cellList = [(3,1)] and column = 5, means rather
                  than looking in cell (3,1) the function will look in cell (3,5)
        tableID:  The HTML id of the table
        first:    Stop on the first match, or find all matches

        Example of use (test url: /inv/warehouse/n/inv_item 
                                 {where n is the warehouse id}
                       ):

            match = dt_find("Plastic Sheets")
            if match:
                if not dt_find(4200, cellList=match, column=5, first=True):
                    assert 0, "Unable to find 4200 Plastic Sheets"
            else:
                assert 0, "Unable to find any Plastic Sheets"

    """

    config = current.test_config
    browser = config.browser

    def find_match(search, tableID, r, c):
        td = ".//*[@id='%s']/tbody/tr[%s]/td[%s]" % (tableID, r, c)
        try:
            elem = browser.find_element_by_xpath(td)
            text = elem.text
            if isinstance(search,(int, float)):
                text = convert_repr_number(text)
            if text == search:
                return (r, c)
        except:
            return False

    result = []
    if cellList:
        for cell in cellList:
            if row:
                r = row
            else:
                r = cell[0]
            if column:
                c = column
            else:
                c = cell[1]
            found =  find_match(search, tableID, r, c)
            if found:
                result.append(found)
                if first:
                    return result

    else:
        # Calculate the rows that need to be navigated along to find the search string
        colList = []
        rowList = []

        if row == None:
            r = 1
            while True:
                tr =  ".//*[@id='%s']/tbody/tr[%s]" % (tableID, r)
                try:
                    elem = browser.find_element_by_xpath(tr)
                    rowList.append(r)
                    r += 1
                except:
                    break
        elif isinstance(row, int):
            rowList = [row]
        else:
            rowList = row
        # Calculate the columns that need to be navigated down to find the search string
        if column == None:
            c = 1
            while True:
                td = ".//*[@id='%s']/tbody/tr[1]/td[%s]" % (tableID, c)
                try:
                    elem = browser.find_element_by_xpath(td)
                    colList.append(c)
                    c += 1
                except:
                    break
        elif isinstance(column, int):
            colList = [column]
        else:
            colList = column
        # Now try and find a match
        for r in rowList:
            for c in colList:
                found =  find_match(search, tableID, r, c)
                if found:
                    result.append(found)
                    if first:
                        return result
    return result
        
# -----------------------------------------------------------------------------
def dt_links(reporter,
             row = 1,
             tableID = "list",
             quiet = True
            ):
    """ Returns a list of links in the given row of the dataTable """

    config = current.test_config
    browser = config.browser

    links = []
    # loop through each column
    column = 1
    while True:
        td =  ".//*[@id='%s']/tbody/tr[%s]/td[%s]" % (tableID, row, column)
        try:
            elem = browser.find_element_by_xpath(td)
        except:
            break
        # loop through looking for links in the cell
        cnt = 1
        while True:
            link = ".//*[@id='%s']/tbody/tr[%s]/td[%s]/a[%s]" % (tableID, row, column, cnt)
            try:
                elem = browser.find_element_by_xpath(link)
            except:
                break
            cnt += 1
            if not quiet:
                reporter("%2d) %s" % (column, elem.text))
            links.append([column,elem.text])
        column += 1
    return links

# -----------------------------------------------------------------------------
def dt_action(row = 1,
              action = None,
              column = 1,
              tableID = "list",
             ):
    """ click the action button in the dataTable """

    config = current.test_config
    browser = config.browser

    # What looks like a fairly fragile xpath, but it should work unless DataTable changes
    if action:
        button = ".//*[@id='%s']/tbody/tr[%s]/td[%s]/a[contains(text(),'%s')]" % (tableID, row, column, action)
    else:
        button = ".//*[@id='%s']/tbody/tr[%s]/td[%s]/a" % (tableID, row, column)
    giveup = 0.0
    sleeptime = 0.2
    while giveup < 10.0:
        try:
            element = browser.find_element_by_xpath(button)
            url = element.get_attribute("href")
            if url:
                browser.get(url)
                return True
        except Exception as inst:
            print "%s with %s" % (type(inst), button)
        time.sleep(sleeptime)
        giveup += sleeptime
    return False
# END =========================================================================