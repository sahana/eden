# -*- coding: utf-8 -*-

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

        TODO implement lookup-method
    """

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

        c = self.canv

        # TODO do this only when self.multiple and only on front-size
        c.setDash(1, 2)
        self.draw_outline()

        w = self.width
        h = self.height

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

            # Get the profile picture
            # TODO look up in bulk
            itable = current.s3db.pr_image
            query = (itable.pe_id == raw["pr_person.pe_id"]) & \
                    (itable.profile == True)
            row = current.db(query).select(itable.image, limitby=(0, 1)).first()
            if row and row.image:
                picture = itable.image.retrieve(row.image)[-1]
                self.draw_image(picture, w * 3 / 4, 165, width=60, height=60, halign="center")

            x = w / 2

            # Name
            name = s3_format_fullname(fname = raw["pr_person.first_name"],
                                      mname = raw["pr_person.middle_name"],
                                      lname = raw["pr_person.last_name"],
                                      truncate = False,
                                      )
            draw_value(x, 134, name, size=10)
            draw_label(x, 134, None, current.T("Name"))

            # Job Title
            draw_field(x, 114, "hrm_human_resource.job_title_id", size=8)
            draw_label(x, 114, "hrm_human_resource.job_title_id")

            # Site (or Branch?)
            # TODO is this the right field? (or should it be branch?)
            draw_field(x, 98, "hrm_human_resource.site_id", size=8)
            draw_label(x, 98, "hrm_human_resource.site_id")

            x = w/4

            # ID (?)
            # TODO identify field
            # TODO use draw_* helpers
            c.setFont(BOLD, 7)
            c.drawCentredString(x, 76, "1-234-567")
            c.setFont(NORMAL, 5)
            c.drawCentredString(x, 70, "Identificación")

            # Blood Type
            # TODO identify field
            # TODO use draw_* helpers
            c.setFont(BOLD, 7)
            c.drawCentredString(x, 58, "O Positivo")
            c.setFont(NORMAL, 5)
            c.drawCentredString(x, 52, "Tipo de Sangre")

            # Issuing Date
            # TODO identify field (use today's date)
            # TODO use draw_* helpers
            c.setFont(BOLD, 7)
            c.drawCentredString(x, 40, "21-Marzo-2018")
            c.setFont(NORMAL, 5)
            c.drawCentredString(x, 34, "Expedido")

            x = w*3/4

            # Volunteer ID
            # TODO only volunteers can have this
            # TODO adjust label?
            draw_field(x, 76, "hrm_human_resource.code")
            draw_label(x, 76, "hrm_human_resource.code")

            # Allergic
            # TODO identify field
            # TODO use draw_* helpers
            c.setFont(BOLD, 7)
            c.drawCentredString(x, 58, "No")
            c.setFont(NORMAL, 5)
            c.drawCentredString(x, 52, "Alergico")

            # Expiration date
            # TODO identify field (lookup interval from org_idcard, then compute)
            # TODO use draw_* helpers
            c.setFont(BOLD, 7)
            c.drawCentredString(x, 40, "21-Marzo-2020")
            c.setFont(NORMAL, 5)
            c.drawCentredString(x, 34, "Expira")

            # Barcode
            # TODO DRY with backside
            code = raw["hrm_human_resource.code"]
            if code:
                self.draw_barcode(s3_str(code), w / 2, 16, height=12, halign="center")

            # Graphics
            if logo:
                self.draw_image(logo, w / 4, 165, width=60, height=60, halign="center")
            c.setFillColor(orange)
            c.rect(0, 0, w, 12, fill=1, stroke=0)
            c.rect(w - 12, 0, 12, 154, fill=1, stroke=0)

        else:
            # TODO Mission statement

            # TODO IFRC membership statement

            # TODO Signature and caption

            # Barcode
            # TODO DRY with backsize
            code = raw["hrm_human_resource.code"]
            if code:
                self.draw_barcode(s3_str(code), w / 2, 16, height=12, halign="center")

            # Graphics
            if logo:
                self.draw_image(logo, w / 2, 170, width=60, height=60, halign="center")
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
