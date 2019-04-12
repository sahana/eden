# -*- coding: utf-8 -*-

import os

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
        Layout for printable beneficiary ID cards
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
                "pe_id",
                "pe_label",
                "first_name",
                "middle_name",
                "last_name",
                "case.organisation_id$root_organisation",
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

        # Get localized root organisation names
        ctable = s3db.br_case
        represent = ctable.organisation_id.represent
        if represent.bulk:
            root_org_names = represent.bulk(list(root_orgs), show_link=False)
        else:
            root_org_names = None

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

        return {"pictures": pictures,
                "root_org_names": root_org_names,
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

        blue = HexColor(0x27548F)

        item = self.item
        raw = item["_row"]

        root_org = raw["org_organisation.root_organisation"]

        # Get the localized root org name
        org_names = common.get("root_org_names")
        if org_names:
            root_org_name = org_names.get(root_org)

        #draw_field = self.draw_field
        draw_value = self.draw_value
        draw_label = self.draw_label

        code = raw["pr_person.pe_label"]

        if not self.backside:

            # Horizontal alignments
            LEFT = w / 4 - 5
            CENTER = w / 2 - 5
            RIGHT = w * 3 / 4 - 5

            # Vertical alignments
            TOP = 200
            #LOWER = [76, 58, 40]
            BOTTOM = 16

            # Organisation name
            if root_org_name:
                draw_value(LEFT, TOP, root_org_name,
                           width = 55,
                           height = 55,
                           size = 10,
                           valign = "middle",
                           )

            # Get the profile picture
            pictures = common.get("pictures")
            if pictures:
                picture = pictures.get(raw["pr_person.pe_id"])
                if picture:
                    self.draw_image(picture, RIGHT, TOP,
                                    width = 60,
                                    height = 55,
                                    valign = "middle",
                                    halign = "center",
                                    )

            # Center fields in reverse order so that vertical positions
            # can be adjusted for very long and hence wrapping strings
            y = 98

            # ID
            ah = draw_value(CENTER, y, code, height=24, size=8)
            draw_label(CENTER, y, None, T("ID Number"))

            # Name
            y += ah + 12
            name = s3_format_fullname(fname = raw["pr_person.first_name"],
                                      mname = raw["pr_person.middle_name"],
                                      lname = raw["pr_person.last_name"],
                                      truncate = False,
                                      )
            draw_value(CENTER, y, name, height=24, size=10)
            draw_label(CENTER, y, None, T("Name"))

            # Barcode
            if code:
                self.draw_barcode(s3_str(code), CENTER, BOTTOM,
                                  height = 12,
                                  halign = "center",
                                  maxwidth = w - 15,
                                  )

            # Graphics
            c.setFillColor(blue)
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

            # QR Code
            if code:
                identity = "%s//%s:%s:%s" % (code,
                                             raw["pr_person.first_name"] or "",
                                             raw["pr_person.middle_name"] or "",
                                             raw["pr_person.last_name"] or "",
                                             )
                self.draw_qrcode(identity, CENTER, MIDDLE,
                                 size=60, halign="center", valign="center")
            # Barcode
            if code:
                self.draw_barcode(s3_str(code), CENTER, BOTTOM,
                                  height = 12,
                                  halign = "center",
                                  maxwidth = w - 15
                                  )

            # Graphics
            c.setFillColor(blue)
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
    def draw_value(self, x, y, value, width=120, height=40, size=7, bold=True, valign=None):
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
            @param valign: vertical alignment ("top"|"middle"|"bottom"),
                           default "bottom"

            @returns: the actual height of the text element drawn
        """

        # Preserve line breaks by replacing them with <br/> tags
        value = s3_str(value).strip("\n").replace('\n','<br />\n')

        stylesheet = getSampleStyleSheet()
        style = stylesheet["Normal"]
        style.fontName = BOLD if bold else NORMAL
        style.fontSize = size
        style.leading = size + 2
        style.splitLongWords = False
        style.alignment = TA_CENTER

        para = Paragraph(value, style)
        aw, ah = para.wrap(width, height)

        while((ah > height or aw > width) and style.fontSize > 4):
            # Reduce font size to make fit
            style.fontSize -= 1
            style.leading = style.fontSize + 2
            para = Paragraph(value, style)
            aw, ah = para.wrap(width, height)

        if valign == "top":
            vshift = ah
        elif valign == "middle":
            vshift = ah / 2.0
        else:
            vshift = 0

        para.drawOn(self.canv, x - para.width / 2, y - vshift)
        return ah

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
