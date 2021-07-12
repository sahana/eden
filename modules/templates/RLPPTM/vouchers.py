# -*- coding: utf-8 -*-

import os

from reportlab.lib.pagesizes import A4
#from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from gluon import current

from s3.codecs.card import S3PDFCardLayout
from s3 import s3_str

# Fonts we use in this layout
NORMAL = "Helvetica"
BOLD = "Helvetica-Bold"

# =============================================================================
class RLPCardLayout(S3PDFCardLayout):
    """
        Parent class for PDF cards to implement common attributes and methods
    """

    cardsize = A4
    orientation = "Portrait"
    doublesided = False

    # -------------------------------------------------------------------------
    def draw_value(self, x, y, value, width=120, height=40, size=7, bold=True, valign=None, halign=None):
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
            @param halign: horizontal alignment ("left"|"center")

            @returns: the actual height of the text element drawn
        """

        # Preserve line breaks by replacing them with <br/> tags
        value = s3_str(value).strip("\n").replace('\n','<br />\n')

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = BOLD if bold else NORMAL
        style.fontSize = size
        style.leading = size + 2
        style.splitLongWords = False
        style.alignment = TA_CENTER if halign=="center" else TA_LEFT

        para = Paragraph(value, style)
        aW, aH = para.wrap(width, height)

        while((aH > height or aW > width) and style.fontSize > 4):
            # Reduce font size to make fit
            style.fontSize -= 1
            style.leading = style.fontSize + 2
            para = Paragraph(value, style)
            aW, aH = para.wrap(width, height)

        if valign == "top":
            vshift = aH
        elif valign == "middle":
            vshift = aH / 2.0
        else:
            vshift = 0

        para.drawOn(self.canv, x - para.width / 2, y - vshift)
        return aH

# =============================================================================
class VoucherCardLayout(RLPCardLayout):
    """
        Layout for printable vouchers
    """

    @classmethod
    def fields(cls, resource):
        """
            The layout-specific list of fields to look up from the resource

            @param resource: the resource

            @returns: list of field selectors
        """

        return ["id",
                "program_id",
                "program_id$name",
                "program_id$organisation_id$name",
                "program_id$organisation_id$root_organisation",
                "program_id$end_date",
                "signature",
                "initial_credit",
                "date",
                "valid_until",
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

        defaultpath = os.path.join(current.request.folder, "uploads")

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

        # Get localized root organisation names
        ctable = s3db.doc_card_config
        represent = ctable.organisation_id.represent
        if represent.bulk:
            root_org_names = represent.bulk(list(root_orgs), show_link=False)
        else:
            root_org_names = None

        # Get voucher instructions from programs
        program_ids = set(item["_row"]["fin_voucher.program_id"] for item in items)
        program_ids.discard(None)
        ptable = s3db.fin_voucher_program
        query = (ptable.id.belongs(program_ids)) & \
                (ptable.voucher_instructions != None) & \
                (ptable.deleted == False)
        programs = db(query).select(ptable.id,
                                    ptable.voucher_instructions,
                                    )
        instructions = {p.id: p.voucher_instructions for p in programs}

        return {"logos": logos,
                "root_org_names": root_org_names,
                "instructions": instructions,
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
        #w = self.width
        h = self.height

        common = self.common

        item = self.item
        raw = item["_row"]

        root_org = raw["org_organisation.root_organisation"]

        # Get the org logo
        logos = common.get("logos")
        logo = logos.get(root_org) if logos else None

        # Get the voucher instructions
        pinst = common.get("instructions")
        instructions = pinst.get(raw["fin_voucher.program_id"])

        draw_value = self.draw_value

        if not self.backside:

            # Program Organisation Logo
            if logo:
                self.draw_image(logo,
                                100,
                                h - 60,
                                width = 120,
                                height = 120,
                                halign = "center",
                                valign = "middle",
                                )

            # Signature QR Code
            signature = s3_str(item.get("fin_voucher.signature"))
            self.draw_qrcode(signature,
                             100,
                             h - 160,
                             size = 120,
                             halign = "center",
                             valign = "middle",
                             level = "M",
                             )

            # Alignments for header items
            HL = 340
            HY = (h - 55, h - 75)

            # Program Organisation
            orgname = s3_str(item.get("org_organisation.name"))
            draw_value(HL, HY[0], orgname, width=280, height=20, size=16)

            # Program Name
            program = s3_str(item.get("fin_voucher_program.name"))
            draw_value(HL, HY[1], program, width=280, height=20, size=12)

            # Alignments for data items
            DL = 250
            DR = 380
            DY = (h - 135, h - 155, h - 175, h - 195)

            # Voucher ID (Signature)
            draw_value(DL, DY[0], "%s:" % T("Voucher ID"), width=100, height=20, size=9, bold=False)
            draw_value(DR, DY[0], signature, width=180, height=20, size=12)

            # Voucher Date
            idate = s3_str(item.get("fin_voucher.date"))
            draw_value(DL, DY[1], "%s:" % T("Issued On"), width=100, height=20, size=9, bold=False)
            draw_value(DR, DY[1], idate, width=180, height=20, size=12)

            # Number of initial credits
            credits = s3_str(item.get("fin_voucher.initial_credit"))
            draw_value(DL, DY[2], "%s:" % T("Number of Beneficiaries"), width=100, height=20, size=9, bold=False)
            draw_value(DR, DY[2], credits, width=180, height=20, size=12)

            # Voucher Valid-until Date
            if raw["fin_voucher.valid_until"]:
                vdate = s3_str(item.get("fin_voucher.valid_until"))
            elif raw["fin_voucher_program.end_date"]:
                vdate = s3_str(item.get("fin_voucher_program.end_date"))
            else:
                vdate = None
            if vdate:
                draw_value(DL, DY[3], "%s:" % T("Valid Until"), width=100, height=20, size=9, bold=False)
                draw_value(DR, DY[3], vdate, width=180, height=20, size=12)

            # Instructions
            if instructions:
                draw_value(285, h-225, instructions, width=450, height=100, size=8, bold=False, valign="top", halign="center")

            # Add a cutting line with multiple cards per page
            if self.multiple:
                c.setDash(1, 2)
                self.draw_outline()
        else:
            # No backside
            pass

# END =========================================================================
