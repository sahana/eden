# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from gluon import current

from s3.codecs.card import S3PDFCardLayout
from s3 import s3_format_fullname, s3_str

# Fonts we use in this layout
NORMAL = "Helvetica"
BOLD = "Helvetica-Bold"

# =============================================================================
class IDCardLayout(S3PDFCardLayout):
    """
        Layout for printable volunteer/staff ID cards
    """

    # -------------------------------------------------------------------------
    @classmethod
    def fields(cls, resource):
        """
            The layout-specific list of fields to look up from the resource

            @param resource: the resource

            @returns: list of field selectors
        """

        return ["id",
                "person_id$pe_id",
                "person_id$first_name",
                "person_id$middle_name",
                "person_id$last_name",
                "person_id$physical_description.blood_type",
                "person_id$physical_description.allergic",
                "person_id$national_id.value",
                "job_title_id",
                "code",
                "organisation_id",
                "organisation_id$name",
                "organisation_id$root_organisation",
                ]

    # -------------------------------------------------------------------------
    @classmethod
    def lookup(cls, resource, items):
        """
            Look up layout-specific common data for all cards

            @param resource: the resource
            @param items: the items

            @returns: a dict with common data
        """

        # TODO look up all org logos

        # TODO look up all profile pictures

        return {}

    # -------------------------------------------------------------------------
    def draw(self):
        """
            TODO cleanup docstring

            Draw the card (one side), to be implemented by subclass

            Instance attributes (NB draw-function should not modify them):
            - self.canv...............the canvas (provides the drawing methods)
            - self.resource...........the resource
            - self.item...............the data item (dict)
            - self.labels.............the field labels (dict)
            - self.backside...........this instance should render the backside
                                      of a card
            - self.multiple...........there are multiple cards per page
            - self.width..............the width of the card (in points)
            - self.height.............the height of the card (in points)

            NB Canvas coordinates are relative to the lower left corner of the
               card's frame, drawing must not overshoot self.width/self.height
        """

        T = current.T

        c = self.canv

        w = self.width
        #h = self.height

        orange = HexColor(0xEE4229)

        item = self.item
        raw = item["_row"]

        root_org = raw["org_organisation.root_organisation"]
        # Get the org logo
        # TODO look up in bulk
        otable = current.s3db.org_organisation
        query = (otable.id == root_org)
        row = current.db(query).select(otable.logo, limitby=(0,1)).first()
        if row and row.logo:
            import os
            logo = os.path.join(otable.logo.uploadfolder, row.logo)
        else:
            logo = None

        if not self.backside:

            draw_field = self.draw_field
            draw_value = self.draw_value
            draw_label = self.draw_label

            # Horizontal alignments
            LEFT = w / 4 - 5
            CENTER = w / 2 - 5
            RIGHT = w * 3 / 4 - 5

            # Vertical alignments
            TOP = 165
            UPPER = [134, 114, 98]
            LOWER = [76, 58, 40]
            BOTTOM = 16

            # Org Logo
            if logo:
                self.draw_image(logo, LEFT, TOP, width=60, height=60, halign="center")

            # Get the profile picture
            # TODO look up in bulk
            itable = current.s3db.pr_image
            query = (itable.pe_id == raw["pr_person.pe_id"]) & \
                    (itable.profile == True)
            row = current.db(query).select(itable.image, limitby=(0, 1)).first()
            if row and row.image:
                picture = itable.image.retrieve(row.image)[-1]
                self.draw_image(picture, RIGHT, TOP, width=60, height=60, halign="center")

            # Name
            name = s3_format_fullname(fname = raw["pr_person.first_name"],
                                      mname = raw["pr_person.middle_name"],
                                      lname = raw["pr_person.last_name"],
                                      truncate = False,
                                      )
            draw_value(CENTER, UPPER[0], name, size=10)
            draw_label(CENTER, UPPER[0], None, T("Name"))

            # Job Title
            draw_field(CENTER, UPPER[1], "hrm_human_resource.job_title_id", size=8)
            draw_label(CENTER, UPPER[1], "hrm_human_resource.job_title_id")

            # Organisation/Branch
            draw_field(CENTER, UPPER[2], "org_organisation.name", size=8)
            draw_label(CENTER, UPPER[2], "hrm_human_resource.organisation_id")

            # IDs
            draw_field(LEFT, LOWER[0], "pr_national_id_identity.value")
            draw_label(LEFT, LOWER[0], None, T("ID"))
            # TODO only volunteers can have this? (Adjust label by HR type?)
            draw_field(RIGHT, LOWER[0], "hrm_human_resource.code")
            draw_label(RIGHT, LOWER[0], None, T("Volunteer ID"))

            # Medical Details
            draw_field(LEFT, LOWER[1], "pr_physical_description.blood_type")
            draw_label(LEFT, LOWER[1], None, T("Blood Type"))
            draw_field(RIGHT, LOWER[1], "pr_physical_description.allergic")
            draw_label(RIGHT, LOWER[1], None, T("Allergic"))

            # Issuing/Expirey Dates
            # TODO adjust interval per org (org_idcard)
            today = current.request.now.date()
            format_date = current.calendar.format_date
            issued_on = format_date(today)
            expires_on = format_date(today + relativedelta(months=24))

            c.setFont(BOLD, 7)
            c.drawCentredString(LEFT, LOWER[2], issued_on)
            draw_label(LEFT, LOWER[2], None, T("Issued on"))
            c.setFont(BOLD, 7)
            c.drawCentredString(RIGHT, LOWER[2], expires_on)
            draw_label(RIGHT, LOWER[2], None, T("Expires on"))

            # Barcode
            code = raw["hrm_human_resource.code"]
            if code:
                self.draw_barcode(s3_str(code), CENTER, BOTTOM, height=12, halign="center")

            # Graphics
            c.setFillColor(orange)
            c.rect(0, 0, w, 12, fill=1, stroke=0)
            c.rect(w - 12, 0, 12, 154, fill=1, stroke=0)

            # Add a utting line with multiple cards per page
            if self.multiple:
                c.setDash(1, 2)
                self.draw_outline()
        else:
            # Horizontal alignments
            CENTER = w / 2

            # Vertical alignments
            TOP = 170
            BOTTOM = 16

            # TODO Mission statement

            # TODO IFRC membership statement

            # TODO Signature and caption

            # Barcode
            code = raw["hrm_human_resource.code"]
            if code:
                self.draw_barcode(s3_str(code), CENTER, BOTTOM, height=12, halign="center")

            # Graphics
            if logo:
                self.draw_image(logo, CENTER, TOP, width=60, height=60, halign="center")
            c.setFillColor(orange)
            c.rect(0, 0, w, 10, fill=1, stroke=0)

    # -------------------------------------------------------------------------
    def draw_field(self, x, y, colname, size=7, bold=True):
        """
            Helper function to draw a centered field value of self.item above
            position (x, y)

            @param x: drawing position
            @param y: drawing position
            @param colname: the column name of the field to look up the value
            @param size: the font size (points)
            @param bold: use bold font
        """

        c = self.canv

        font = BOLD if bold else NORMAL

        value = self.item.get(colname)
        if value:
            c.setFont(font, size)
            c.drawCentredString(x, y, s3_str(value))

    # -------------------------------------------------------------------------
    def draw_value(self, x, y, value, width=120, height=40, size=7, bold=True):
        """
            Helper function to draw a centered text above position (x, y);
            allows the text to wrap if it would otherwise exceed the given
            width

            @param x: drawing position
            @param y: drawing position
            @param value: the text to render
            @param width: the maximum available width (points)
            @param height: the maximum available height (points)
            @param size: the font size (points)
            @param bold: use bold font
        """

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = BOLD if bold else NORMAL
        style.fontSize = size
        style.alignment = TA_CENTER

        para = Paragraph(value, style)
        # TODO verify that para does not need to split?
        para.wrap(width, height)
        para.drawOn(self.canv, x - para.width / 2, y)

    # -------------------------------------------------------------------------
    def draw_label(self, x, y, colname, default=""):
        """
            Helper function to draw a centered label below position (x, y)

            @param x: drawing position
            @param y: drawing position
            @param colname: the column name of the field to look up the label
            @param default: the default label (if label cannot be looked up),
                            pass colname=None to enforce using the default
        """

        if colname:
            label = self.labels.get(colname, default)
        else:
            label = default

        c = self.canv
        c.setFont(NORMAL, 5)
        c.drawCentredString(x, y - 6, s3_str(label))

# END =========================================================================
