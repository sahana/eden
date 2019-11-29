# -*- coding: utf-8 -*-

"""
    S3Codec to produce printable data cards (e.g. ID cards)

    @copyright: 2018-2019 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3PDFCard",
           )

try:
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Flowable, \
                                   Frame, NextPageTemplate, PageBreak
    from reportlab.lib.utils import ImageReader
    from reportlab.graphics import renderPDF
    from reportlab.graphics.barcode import code39, code128, qr
    from reportlab.graphics.shapes import Drawing
    REPORTLAB = True
except ImportError:
    BaseDocTemplate = object
    Flowable = object
    REPORTLAB = False

from gluon import current, HTTP

from s3compat import BytesIO
from ..s3codec import S3Codec
from ..s3resource import S3Resource
from ..s3utils import s3_str

CREDITCARD = (153, 243) # Default format for cards (in points)
# =============================================================================
class S3PDFCard(S3Codec):
    """
        Codec to produce printable data cards (e.g. ID cards)
    """

    def encode(self, resource, **attr):
        """
            API Method to encode a resource as cards

            @param resource: the S3Resource, or
                             - the data items as list [{fieldname: representation, ...}, ...], or
                             - a callable that produces such a list of items
            @param attr: additional encoding parameters (see below)

            @keyword layout: the layout (a S3PDFCardLayout subclass, overrides
                             the resource's pdf_card_layout setting
            @keyword orderby: orderby-expression for data extraction, overrides
                              the resource's orderby setting
            @keyword labels: the labels for the fields,
                             - a dict {colname: label}, or
                             - a callable that produces it,
                             - defaults to the labels of the extracted fields
            @keyword pagesize: the PDF page size,
                               - a string "A4" or "Letter", or
                               - a tuple (width, height), in points
                               - defaults to the layout's card size
            @keyword margins: the page margins,
                              - a tuple (N, E, S, W), in points, or
                              - a single number, in points
                              - will be computed if omitted
            @keyword spacing: the spacing between cards,
                              - a tuple (H, V), in points, or
                              - a single number, in points
                              - defaults to 18 points in both directions
            @keyword title: the document title,
                            - defaults to title_list crud string of the resource

            @return: a handle to the output
        """

        if not REPORTLAB:
            # FIXME is this the correct handling of a dependency failure?
            raise HTTP(503, "Python ReportLab library not installed")

        # Do we operate on a S3Resource?
        is_resource = isinstance(resource, S3Resource)

        # The card layout
        layout = attr.get("layout")
        if layout is None and is_resource:
            layout = resource.get_config("pdf_card_layout")
        if layout is None:
            layout = S3PDFCardLayout

        # Card (and hence page) orientation
        orientation = layout.orientation
        if orientation == "Landscape":
            orientation = landscape
        else:
            orientation = portrait

        # Card and page size
        cardsize = orientation(layout.cardsize)
        pagesize = attr.get("pagesize")
        if pagesize == "A4":
            pagesize = A4
        elif pagesize == "Letter":
            pagesize = LETTER
        elif not isinstance(pagesize, (tuple, list)):
            pagesize = cardsize
        pagesize = orientation(pagesize)

        # Extract the data
        if is_resource:
            # Extract the data items from the resource
            fields = layout.fields(resource)
            data = self.extract(resource, fields, orderby=attr.get("orderby"))
            items = data.rows
        elif callable(resource):
            # External getter => call with resource, returns the data items
            data = None
            items = resource()
        else:
            # The data items have been passed-in in place of the resource
            data = None
            items = resource

        # Get the labels
        labels = attr.get("labels")
        if callable(labels):
            labels = labels(resource)
        elif not isinstance(labels, dict):
            if data and hasattr(data, "rfields"):
                # Collect the labels from rfields
                rfields = data.rfields
                labels = {rfield.colname: rfield.label for rfield in rfields}
            else:
                labels = {}


        # Document title
        title = attr.get("title")
        if not title and is_resource:
            crud_strings = current.response.s3.crud_strings[resource.tablename]
            if crud_strings:
                title = crud_strings["title_list"]

        # Instantiate the doc template
        doc = S3PDFCardTemplate(pagesize,
                                cardsize,
                                margins = attr.get("margins"),
                                spacing = attr.get("spacing"),
                                title = title,
                                )

        # Produce the flowables
        flowables = self.get_flowables(layout,
                                       resource,
                                       items,
                                       labels = labels,
                                       cards_per_page = doc.cards_per_page,
                                       )

        # Build the doc
        output_stream = BytesIO()
        doc.build(flowables,
                  output_stream,
                  #canvasmaker=canvas.Canvas,   # is default
                  )

        output_stream.seek(0)
        return output_stream

    # -------------------------------------------------------------------------
    @staticmethod
    def extract(resource, fields, orderby=None):
        """
            Extract the data items from the given resource

            @param resource: the resource (a filtered S3Resource)
            @param fields: the fields to extract (array of field selectors)
            @param orderby: the orderby-expression

            @returns: an S3ResourceData instance
        """

        if orderby is None:
            orderby = resource.get_config("orderby")
        if orderby is None:
            orderby = resource._id

        return resource.select(fields,
                               represent = True,
                               show_links = False,
                               raw_data = True,
                               orderby = orderby,
                               )

    # -------------------------------------------------------------------------
    @staticmethod
    def get_flowables(layout, resource, items, labels=None, cards_per_page=1):
        """
            Get the Flowable-instances for the data items

            @param layout: the S3PDFCardLayout subclass implementing the
                           card layout
            @param resource: the resource
            @param items: the data items
            @param labels: the field labels
            @param cards_per_page: the number of cards per page
        """

        if not len(items):
            # Need at least one flowable even to produce an empty doc
            return [PageBreak()]

        # Determine the number of pages
        number_of_pages = int(len(items) / cards_per_page) + 1
        multiple = cards_per_page > 1

        # Look up common data
        common = layout.lookup(resource, items)

        # Generate the pages
        flowables = []
        append = flowables.append
        for i in range(number_of_pages):

            # Get the items for the current page
            batch = items[i * cards_per_page:(i+1) * cards_per_page]
            if not batch:
                continue

            # Add the flowables for the card fronts to the page
            append(NextPageTemplate("Front"))
            if i > 0:
                append(PageBreak())
            for item in batch:
                append(layout(resource,
                              item,
                              labels = labels,
                              common = common,
                              multiple = multiple,
                              ))

            if layout.doublesided:
                # Add the flowables for the backsides on a new page
                append(NextPageTemplate("Back"))
                append(PageBreak())
                for item in batch:
                    append(layout(resource,
                                  item,
                                  labels = labels,
                                  common = common,
                                  multiple = multiple,
                                  backside = True,
                                  ))

        return flowables

# =============================================================================
class S3PDFCardTemplate(BaseDocTemplate):
    """
        Document Template for data cards
    """

    def __init__(self,
                 pagesize,
                 cardsize,
                 margins = None,
                 spacing = None,
                 title = None,
                 ):
        """
            Constructor

            @param pagesize: the page size, tuple (w, h)
            @param cardsize: the card size, tuple (w, h)
            @param margins: the page margins, tuple (N, E, S, W)
            @param spacing: the spacing between cards, tuple (H, V)
            @param title: the document title

            - all sizes in points (72 points per inch)
        """

        # Spacing between cards
        if spacing is None:
            spacing = (18, 18)
        elif not isinstance(spacing, (tuple, list)):
            spacing = (spacing, spacing)

        # Page margins
        if margins is None:
            margins = self.compute_margins(pagesize, cardsize, spacing)
        elif not isinstance(margins, (tuple, list)):
            margins = (margins, margins, margins, margins)

        # Cards per row, rows per page and cards per page
        pagewidth, pageheight = pagesize
        cardwidth, cardheight = cardsize

        number_of_cards = self.number_of_cards

        cards_per_row = number_of_cards(pagewidth,
                                        cardwidth,
                                        (margins[1], margins[3]),
                                        spacing[0],
                                        )

        rows_per_page = number_of_cards(pageheight,
                                        cardheight,
                                        (margins[0], margins[2]),
                                        spacing[1],
                                        )

        self.cards_per_row = cards_per_row
        self.rows_per_page = rows_per_page
        self.cards_per_page = rows_per_page * cards_per_row

        # Generate page templates
        pages = self.page_layouts(pagesize, cardsize, margins, spacing)

        if title is None:
            title = current.T("Items")

        # Call super-constructor
        BaseDocTemplate.__init__(self,
                                 None,
                                 pagesize = pagesize,
                                 pageTemplates = pages,
                                 topMargin = margins[0],
                                 rightMargin = margins[1],
                                 bottomMargin = margins[2],
                                 leftMargin = margins[3],
                                 title = s3_str(title),
                                 )

    # -------------------------------------------------------------------------
    @staticmethod
    def number_of_cards(pagesize, cardsize, margins, spacing):
        """
            Compute the number of cards for one page dimension

            @param pagesize: the page size
            @param cardsize: the card size
            @param margins: tuple of margins
            @param spacing: the spacing between cards
        """

        available = pagesize - sum(margins)
        if available < cardsize:
            available = pagesize
        if available < cardsize:
            return 0
        return int((available + spacing) / (cardsize + spacing))

    # -------------------------------------------------------------------------
    def compute_margins(self, pagesize, cardsize, spacing):
        """
            Calculate default margins

            @param pagesize: the page size, tuple (w, h)
            @param cardsize: the card size, tuple (w, h)
            @param spacing: spacing between cards, tuple (h, v)
        """

        cardwidth, cardheight = cardsize
        pagewidth, pageheight = pagesize
        spacing_h, spacing_v = spacing

        # Calculate number of cards with minimal margins
        number_of_cards = self.number_of_cards
        numh = number_of_cards(pagewidth, cardwidth, (18, 18), spacing_h)
        numv = number_of_cards(pageheight, cardheight, (12, 12), spacing_v)

        # Compute total width/height of as many cards
        width = (numh - 1) * (cardwidth + spacing_h) + cardwidth
        height = (numv - 1) * (cardheight + spacing_v) + cardheight

        # Compute the actual margins, centering the cards on the page
        margin_h = (pagewidth - width) / 2
        margin_v = (pageheight - height) / 2

        return (margin_v, margin_h, margin_v, margin_h)

    # -------------------------------------------------------------------------
    def page_layouts(self, pagesize, cardsize, margins, spacing):
        """
            Generate page templates for front/back sides of cards

            @param pagesize: the page size, tuple (w, h)
            @param cardsize: the card size, tuple (w, h)
            @param margins: the page margins, tuple (N, E, S, W)
            @param spacing: the spacing between cards, tuple (H, V)

            - all sizes in points (72 points per inch)
        """

        pagewidth, pageheight = pagesize
        cardwidth, cardheight = cardsize

        topmargin, leftmargin = margins[0], margins[3]

        hspacing, vspacing = spacing

        # Y-position (from page bottom) of first card row
        y0 = pageheight - topmargin - cardheight

        # X-position of first card in a row
        # - front from the left, back from the right
        # - actual page width differs between printers, so we may need
        #   to add a parameter to account for this horizontal shift (TODO)
        x0_front = leftmargin
        x0_back = pagewidth - leftmargin - cardwidth # + hshift

        fframes, bframes = [], []
        for i in range(self.rows_per_page):

            # Y-position of current row
            y = y0 - i * (vspacing + cardheight)

            # Add frames for cards in this row
            for j in range(self.cards_per_row):

                # Front
                fframes.append(Frame(x0_front + j * (cardwidth + hspacing),
                                     y,
                                     cardwidth,
                                     cardheight,
                                     topPadding = 0,
                                     rightPadding = 0,
                                     bottomPadding = 0,
                                     leftPadding = 0,
                                     ))

                # Back
                bframes.append(Frame(x0_back - j * (cardwidth + hspacing),
                                     y,
                                     cardwidth,
                                     cardheight,
                                     topPadding = 0,
                                     rightPadding = 0,
                                     bottomPadding = 0,
                                     leftPadding = 0,
                                     ))

        # Generate and return the page templates
        return [PageTemplate(id="Front", frames = fframes),
                PageTemplate(id="Back", frames = bframes),
                ]

# =============================================================================
class S3PDFCardLayout(Flowable):
    """
        Flowable base class for data cards, to be subclassed per use-case;
        subclasses should implement the draw()-method to render a data item.
    """

    # Card layout parameters (subclasses can override this)
    cardsize = CREDITCARD
    orientation = "Portrait"
    doublesided = True

    def __init__(self,
                 resource,
                 item,
                 labels=None,
                 common=None,
                 backside=False,
                 multiple=False,
                 ):
        """
            Constructor

            @param resource: the resource
            @param item: the data item
            @param labels: the field labels
            @param common: common data for all cards
            @param backside: this instance should render a card backside
            @param multiple: there are multiple cards per page
        """

        Flowable.__init__(self)

        self.width, self.height = self.cardsize

        self.resource = resource
        self.item = item

        self.labels = labels if labels is not None else {}
        self.common = common if common is not None else {}

        self.backside = backside
        self.multiple = multiple

    # -------------------------------------------------------------------------
    def draw(self):
        """
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

        w = self.width
        h = self.height

        c.setDash(1, 2)
        self.draw_outline()

        x = w / 2
        y = h / 2

        c.setFont("Helvetica", 12)
        c.drawCentredString(x, y, "Back" if self.backside else "Front")

        resource = self.resource
        if isinstance(resource, S3Resource):
            # Render the record ID if available
            item = self.item
            pid = str(resource._id)
            if pid in item:
                c.setFont("Helvetica", 8)
                c.drawCentredString(x, y - 10, "Record #%s" % item[pid])

    # -------------------------------------------------------------------------
    @classmethod
    def fields(cls, resource):
        """
            Get the fields to look up from the resource, can be overridden
            in subclasses (as the field list is usually layout-specific)

            @param resource: the resource

            @returns: list of field selectors
        """

        return resource.list_fields()

    # -------------------------------------------------------------------------
    @classmethod
    def lookup(cls, resource, items):
        """
            Look up common data for all cards

            @param resource: the resource
            @param items: the items

            @returns: a dict with common data for all cards, will be
                      passed to the individual flowables
        """

        return {}

    # -------------------------------------------------------------------------
    def draw_barcode(self,
                     value,
                     x,
                     y,
                     bctype="code128",
                     height=12,
                     barwidth=0.85,
                     halign=None,
                     valign=None,
                     maxwidth=None,
                     ):
        """
            Helper function to render a barcode

            @param value: the string to encode
            @param x: drawing position
            @param y: drawing position
            @param bctype: the barcode type
            @param height: the height of the barcode (in points)
            @param barwidth: the default width of the smallest bar
            @param halign: horizontal alignment ("left"|"center"|"right"), default left
            @param valign: vertical alignment ("top"|"middle"|"bottom"), default bottom
            @param maxwidth: the maximum total width, if specified, the barcode will
                             not be rendered if it would exceed this width even with
                             the minimum possible bar width

            @return: True if successful, otherwise False
        """

        # For arbitrary alphanumeric values, these would be the most
        # commonly used symbologies:
        types = {"code39": code39.Standard39,
                 "code128": code128.Code128,
                 }

        encode = types.get(bctype)
        if not encode:
            raise RuntimeError("Barcode type %s not supported" % bctype)
        else:
            qz = 12 * barwidth
            barcode = encode(value,
                             barHeight = height,
                             barWidth = barwidth,
                             lquiet = qz,
                             rquiet = qz,
                             )

        width, height = barcode.width, barcode.height
        if maxwidth and width > maxwidth:
            # Try to adjust the bar width
            bw = max(float(maxwidth) / width * barwidth, encode.barWidth)
            qz = 12 * bw
            barcode = encode(value,
                             barHeight = height,
                             barWidth = bw,
                             lquiet = qz,
                             rquiet = qz,
                             )
            width = barcode.width
            if width > maxwidth:
                return False

        hshift = vshift = 0
        if halign == "right":
            hshift = width
        elif halign == "center":
            hshift = width / 2.0

        if valign == "top":
            vshift = height
        elif valign == "middle":
            vshift = height / 2.0

        barcode.drawOn(self.canv, x - hshift, y - vshift)
        return True

    # -------------------------------------------------------------------------
    def draw_qrcode(self, value, x, y, size=40, halign=None, valign=None):
        """
            Helper function to draw a QR code

            @param value: the string to encode
            @param x: drawing position
            @param y: drawing position
            @param size: the size (edge length) of the QR code
            @param halign: horizontal alignment ("left"|"center"|"right"), default left
            @param valign: vertical alignment ("top"|"middle"|"bottom"), default bottom
        """

        qr_code = qr.QrCodeWidget(value)

        try:
            bounds = qr_code.getBounds()
        except ValueError:
            # Value contains invalid characters
            return

        w = bounds[2] - bounds[0]
        h = bounds[3] - bounds[1]

        transform = [float(size) / w, 0, 0, float(size) / h, 0, 0]
        d = Drawing(size, size, transform=transform)
        d.add(qr_code)

        hshift = vshift = 0
        if halign == "right":
            hshift = size
        elif halign == "center":
            hshift = float(size) / 2.0

        if valign == "top":
            vshift = size
        elif valign == "middle":
            vshift = float(size) / 2.0

        renderPDF.draw(d, self.canv, x - hshift, y - vshift)

    # -------------------------------------------------------------------------
    def draw_image(self,
                   img,
                   x,
                   y,
                   width=None,
                   height=None,
                   proportional=True,
                   scale=None,
                   halign=None,
                   valign=None,
                   ):
        """
            Helper function to draw an image
            - requires PIL (required for ReportLab image handling anyway)

            @param img: the image (filename or BytesIO buffer)
            @param x: drawing position
            @param y: drawing position
            @param width: the target width of the image (in points)
            @param height: the target height of the image (in points)
            @param proportional: keep image proportions when scaling to width/height
            @param scale: scale the image by this factor (overrides width/height)
            @param halign: horizontal alignment ("left"|"center"|"right"), default left
            @param valign: vertical alignment ("top"|"middle"|"bottom"), default bottom
        """

        if hasattr(img, "seek"):
            is_buffer = True
            img.seek(0)
        else:
            is_buffer = False

        try:
            from PIL import Image as pImage
        except ImportError:
            current.log.error("Image rendering failed: PIL not installed")
            return

        pimg = pImage.open(img)
        img_size = pimg.size

        if not img_size[0] or not img_size[1]:
            # This image has at least one dimension of zero
            return

        # Compute drawing width/height
        if scale:
            width = img_size[0] * scale
            height = img_size[1] * scale
        elif width and height:
            if proportional:
                scale = min(float(width) / img_size[0], float(height) / img_size[1])
                width = img_size[0] * scale
                height = img_size[1] * scale
        elif width:
            height = img_size[1] * (float(width) / img_size[0])
        elif height:
            width = img_size[0] * (float(height) / img_size[1])
        else:
            width = img_size[0]
            height = img_size[1]

        # Compute drawing position from alignment options
        hshift = vshift = 0
        if halign == "right":
            hshift = width
        elif halign == "center":
            hshift = width / 2.0

        if valign == "top":
            vshift = height
        elif valign == "middle":
            vshift = height / 2.0

        # Draw the image
        if is_buffer:
            img.seek(0)
        ir = ImageReader(img)

        c = self.canv
        c.drawImage(ir,
                    x - hshift,
                    y - vshift,
                    width = width,
                    height = height,
                    preserveAspectRatio = proportional,
                    mask = "auto",
                    )

    # -------------------------------------------------------------------------
    def draw_outline(self):
        """
            Helper function to draw the outline of the card, useful as cutting
            line when there are multiple cards per page
        """

        c = self.canv

        c.setLineWidth(1)
        c.rect(-1, -1, self.width + 2, self.height + 2)

# END =========================================================================
