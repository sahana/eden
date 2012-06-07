import os
import time

from selenium.common.exceptions import NoSuchElementException

from gluon import current

from s3 import s3_debug
from tests.web2unittest import SeleniumUnitTest

class Org_Organisation(SeleniumUnitTest):

    # -------------------------------------------------------------------------
    def test_create_organisation(self, items=[0]):
        """
            Create an Organisation
            
            @param items: Organisation(s) to create from the data

            @ToDo: currently optimised for a single record
        """
        print "\n"

        # Configuration
        tablename = "org_organisation"
        url = "org/organisation/create"
        account = "normal"
        data = current.data["organisation"]

        for item in items:
            _data = data[item]
            # Check whether the data already exists
            s3db = current.s3db
            db = current.db
            table = s3db[tablename]
            fieldname = _data[0][0]
            value = _data[0][1]
            query = (table[fieldname] == value) & (table.deleted == "F")
            record = db(query).select(table.id,
                                      limitby=(0, 1)).first()
            if record:
                print "org_create_organisation skipped as %s already exists in the db\n" % value
                return False

            # Login, if not-already done so
            self.login(account=account, nexturl=url)

            # Create a record using the data
            result = self.create(tablename, _data)

    # -------------------------------------------------------------------------
    def test_add_logo(self):
        """
            This will open up an existing organisation and add a logo
        """

        nexturl = "org/organisation/"
        account = "admin"
        dataList = [
                    {"org" : "Afghan Red Crescent Society",
                     "logo" : "icrc-cl.gif"
                    },
                    {"org" : "International Federation of Red Cross and Red Crescent Societies",
                     "logo" : "icrc.gif"
                    },
                   ]

        s3db = current.s3db
        db = current.db
        table = s3db.org_organisation
        itable = s3db.pr_image_library
        browser = self.browser
        for data in dataList:
            # Go to the organisation list page
            self.login(account=account, nexturl=nexturl)
            # Find the org in the dataTable (filter so only one is displayed)
            self.dt_filter(data["org"])
            # Open the org (the first - and only - by default)
            self.dt_action()
            # Add the logo to the org
            el = browser.find_element_by_id("org_organisation_logo")
            logo_path = os.path.join(self.config.base_dir,
                                     "private", "templates", "regression",
                                     data["logo"])
            s3_debug("Logo path: %s" % logo_path)
            el.send_keys(logo_path)
            # Now get the org id from the url before we save the form
            url = browser.current_url
            url_parts = url.split("/")
            org_id = url_parts[-2]
            # Submit the Form
            browser.find_element_by_css_selector("input[type='submit']").click()
            # Check & Report the results
            confirm = True
            try:
                elem = browser.find_element_by_xpath("//div[@class='confirmation']")
                s3_debug(elem.text)
            except NoSuchElementException:
                confirm = False
            self.assertTrue(confirm == True,
                            "Unable to add a logo to %s" % data["org"])
            # Need to check that the logo has been added to the table
            query = (table.id == org_id) & (table.deleted == "F")
            record = db(query).select(limitby=(0, 1)).first()
            logo = record.logo
            self.assertTrue(logo,
                            "The logo is not in the database for %s" % data["org"])
            s3_debug("logo file upload with the new file name of %s" % logo)
            # Check that the extra images are also created
            query = (itable.original_name == logo)
            extra_images = db(query).count()
            self.assertTrue(extra_images == 2,
                            "The expected extra logos were not added to the image library")
            s3_debug("Two extra logos were created")
                 

# END =========================================================================
