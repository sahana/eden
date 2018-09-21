# -*- coding: utf-8 -*-

import os

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

        db = current.db
        s3db = current.s3db

        defaultpath = os.path.join(current.request.folder, 'uploads')

        # Get all root organisations
        root_orgs = set(item["_row"]["org_organisation.root_organisation"]
                        for item in items)

        # Look up all logos
        otable = s3db.org_organisation
        query = (otable.id.belongs(root_orgs))
        rows = db(query).select(otable.id, otable.logo)

        field = otable.logo
        path = field.uploadfolder if field.uploadfolder else defaultpath
        logos = {row.id: os.path.join(path, row.logo) for row in rows if row.logo}

        # Look up VOLID card configs for all root orgs
        ctable = s3db.doc_card_config
        query = (ctable.card_type == "VOLID") & \
                (ctable.organisation_id.belongs(root_orgs)) & \
                (ctable.deleted == False)
        configs = db(query).select(ctable.organisation_id,
                                   ctable.authority_statement,
                                   ctable.org_statement,
                                   ctable.signature,
                                   ctable.signature_text,
                                   ctable.validity_period,
                                   ).as_dict(key="organisation_id")

        # Get all PE IDs
        pe_ids = set(item["_row"]["pr_person.pe_id"] for item in items)

        # Look up all profile pictures
        itable = s3db.pr_image
        query = (itable.pe_id.belongs(pe_ids)) & \
                (itable.profile == True) & \
                (itable.deleted == False)
        rows = db(query).select(itable.pe_id, itable.image)

        field = itable.image
        path = field.uploadfolder if field.uploadfolder else defaultpath
        pictures = {row.pe_id: os.path.join(path, row.image) for row in rows if row.image}

        return {"logos": logos,
                "pictures": pictures,
                "configs": configs,
                }

    # -------------------------------------------------------------------------
    def draw(self):
        """
            Draw the card (one side)

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
        common = self.common

        orange = HexColor(0xEE4229)

        item = self.item
        raw = item["_row"]

        root_org = raw["org_organisation.root_organisation"]

        # Get the org logo
        logos = common.get("logos")
        if logos:
            logo = logos.get(root_org)
        else:
            logo = None

        # Get the root org's card configuration
        configs = common.get("configs")
        if configs:
            config = configs.get(root_org)
        else:
            config = None

        draw_field = self.draw_field
        draw_value = self.draw_value
        draw_label = self.draw_label

        if not self.backside:

            # Horizontal alignments
            LEFT = w / 4 - 5
            CENTER = w / 2 - 5
            RIGHT = w * 3 / 4 - 5

            # Vertical alignments
            TOP = 200
            LOWER = [76, 58, 40]
            BOTTOM = 16

            # Org Logo
            if logo:
                self.draw_image(logo, LEFT, TOP, width=60, height=60, valign="middle", halign="center")

            # Get the profile picture
            pictures = common.get("pictures")
            if pictures:
                picture = pictures.get(raw["pr_person.pe_id"])
                if picture:
                    self.draw_image(picture, RIGHT, TOP, width=60, height=60, valign="middle", halign="center")

            # Center fields in reverse order so that vertical positions
            # can be adjusted for very long and hence wrapping strings
            y = 98

            # Organisation/Branch
            org_name = s3_str(item.get("org_organisation.name"))
            aH = draw_value(CENTER, y, org_name, height=16, size=8)
            draw_label(CENTER, y, "hrm_human_resource.organisation_id")

            # Job Title
            y += aH + 12
            job_title = s3_str(item.get("hrm_human_resource.job_title_id"))
            aH = draw_value(CENTER, y, job_title, height=16, size=8)
            draw_label(CENTER, y, "hrm_human_resource.job_title_id")

            # Name
            y += aH + 12
            name = s3_format_fullname(fname = raw["pr_person.first_name"],
                                      mname = raw["pr_person.middle_name"],
                                      lname = raw["pr_person.last_name"],
                                      truncate = False,
                                      )
            draw_value(CENTER, y, name, height=24, size=10)
            draw_label(CENTER, y, None, T("Name"))

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
            vp = config.get("validity_period", 24) if config else 24
            today = current.request.now.date()
            format_date = current.calendar.format_date
            issued_on = format_date(today)
            expires_on = format_date(today + relativedelta(months=vp))

            c.setFont(BOLD, 7)
            c.drawCentredString(LEFT, LOWER[2], issued_on)
            draw_label(LEFT, LOWER[2], None, T("Issued on"))
            c.setFont(BOLD, 7)
            c.drawCentredString(RIGHT, LOWER[2], expires_on)
            draw_label(RIGHT, LOWER[2], None, T("Expires on"))

            # Barcode
            code = raw["hrm_human_resource.code"]
            if code:
                self.draw_barcode(s3_str(code), CENTER, BOTTOM,
                                  height = 12,
                                  halign = "center",
                                  maxwidth = w - 15,
                                  )

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
            TOP = 200
            MIDDLE = 85
            BOTTOM = 16

            if config:
                # Organisation Statement
                org_statement = config.get("org_statement")
                if org_statement:
                    aH = draw_value(CENTER,
                                    MIDDLE,
                                    org_statement,
                                    height = 40,
                                    size = 6,
                                    )

                # Authority Statement
                authority_statement = config.get("authority_statement")
                if authority_statement:
                    draw_value(CENTER,
                               MIDDLE + aH + 10,
                               authority_statement,
                               height = 40,
                               size = 7,
                               bold = False,
                               )

                # Signature
                signature = config.get("signature")
                if signature:
                    field = current.s3db.doc_card_config.signature
                    path = field.uploadfolder
                    if not path:
                        path = os.path.join(current.request.folder, 'uploads')
                    self.draw_image(os.path.join(path, signature),
                                    CENTER,
                                    MIDDLE - 15,
                                    height = 40,
                                    width = 60,
                                    valign = "middle",
                                    halign = "center",
                                    )

                # Signature Text
                signature_text = config.get("signature_text")
                if signature_text:
                    draw_value(CENTER,
                               MIDDLE - (45 if signature else 25),
                               signature_text,
                               height = 20,
                               size = 5,
                               bold = False,
                               )

            # Barcode
            code = raw["hrm_human_resource.code"]
            if code:
                self.draw_barcode(s3_str(code), CENTER, BOTTOM,
                                  height = 12,
                                  halign = "center",
                                  maxwidth = w - 15
                                  )

            # Graphics
            if logo:
                self.draw_image(logo, CENTER, TOP, width=60, height=60, valign="middle", halign="center")
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

            @returns: the actual height of the text element drawn
        """

        # Preserve line breaks by replacing them with <br/> tags
        value = value.strip("\n").replace('\n','<br />\n')

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = BOLD if bold else NORMAL
        style.fontSize = size
        style.leading = size + 2
        style.alignment = TA_CENTER

        para = Paragraph(value, style)
        aH = para.wrap(width, height)[1]

        while(aH > height and style.fontSize > 4):
            # Reduce font size to make fit
            style.fontSize -= 1
            style.leading = style.fontSize + 2
            para = Paragraph(value, style)
            aH = para.wrap(width, height)[1]

        para.drawOn(self.canv, x - para.width / 2, y)
        return aH

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
