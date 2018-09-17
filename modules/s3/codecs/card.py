# -*- coding: utf-8 -*-

"""
    S3Codec to produce printable ID cards

    @copyright: 2018 (c) Sahana Software Foundation
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

__all__ = ("S3IDCard",
           )

try:
    from cStringIO import StringIO    # Faster, where available
except ImportError:
    from StringIO import StringIO

try:
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Flowable, \
                                   Frame, NextPageTemplate, PageBreak
    REPORTLAB = True
except ImportError:
    BaseDocTemplate = object
    REPORTLAB = False

from gluon import current, HTTP

from ..s3codec import S3Codec

# =============================================================================
class S3IDCard(S3Codec):
    """
        Codec to produce printable ID cards
    """

    def __init__(self):
        """
            Constructor

            TODO implement

            Parameters needed:
                - card size (default to 153x243 points)
                - page size and orientation (default to card size)
                - margins (should default)
                - spacing (should default)
                - fields to extract, or an external data extraction method
                - labels, or an external getter
                - designs for front and back (or just front)
                - other options
        """

        pass

    # -------------------------------------------------------------------------
    def encode(self, resource, **attr):
        """
            API Method to encode an ElementTree into the target format,
            to be implemented by the subclass

            @param resource: the S3Resource

            @return: a handle to the output
        """

        if not REPORTLAB:
            # FIXME is this the correct handling of a dependency failure?
            raise HTTP(503, "Python ReportLab library not installed")

        # 1. Extract the data               TODO

        # If we have a list of fields
        #   => use Resource.select
        # else:
        #   => call the getter

        # Get the labels
        # => can be a getter
        # => can be a dict
        # => default to labels in rfields-attribute of data returned from extract
        # => fall back to no labels (empty dict)

        # Initialize the output stream
        output_stream = StringIO()

        # 3. Instantiate the doc template   TODO
        size = (153, 243)
        doc = S3IDCardDocTemplate(size, (153,243)) #, margins=(0, 0, 0, 0), spacing=(0,0))

        # 4. Produce the flowables          TODO
        flowables = self.get_flowables([None,
                                        None,
                                        None,
                                        None,
                                        None,
                                        ],
                                        labels = {},
                                        # TODO pass in doc.cards_per_page
                                        cards_per_row = doc.cards_per_row,
                                        rows_per_page = doc.rows_per_page,
                                        )

        # 5. Build the doc                  TODO
        doc.build(flowables,
                  #output_stream,
                  "test.pdf",
                  #canvasmaker=canvas.Canvas,
                  )

        return output_stream

    # -------------------------------------------------------------------------
    def get_flowables(self, items, labels, cards_per_row=1, rows_per_page=1):
        # TODO docstring
        # TODO pass in doc to extract cards_per_page

        cards_per_page = rows_per_page * cards_per_row
        number_of_batches = int(len(items) / cards_per_page) + 1

        flowables = []
        append = flowables.append
        for i in range(number_of_batches):

            batch = items[i * cards_per_page:(i+1) * cards_per_page]
            if not batch:
                continue

            append(NextPageTemplate("Front"))
            if i > 0:
                append(PageBreak())
            for item in batch:
                # TODO parametrize front-flowable class
                append(S3IDCardFlowable(item))

            # TODO make conditional (single/double-sided)
            append(NextPageTemplate("Back"))
            append(PageBreak())
            for item in batch:
                # TODO parametrize back-flowable class
                append(S3IDCardFlowable(item, backside=True))

        return flowables

    # -------------------------------------------------------------------------
    def decode(self, resource, source, **attr):
        """
            API Method to decode a source into an ElementTree, to be
            implemented by the subclass
            TODO fix docstring, explain this function

            @param resource: the S3Resource
            @param source: the source

            @return: an S3XML ElementTree
        """
        return current.xml.tree()

# =============================================================================
class S3IDCardDocTemplate(BaseDocTemplate):
    """
        Document Template for ID cards
    """

    def __init__(self,
                 pagesize,
                 cardsize,
                 margins = None,
                 spacing = None,
                 ):
        """
            Constructor

            @param pagesize: the page size, tuple (width, height) in points
            @param cardsize: the card size, tuple (width, height) in points
            @param margins: the page margins, tuple (N, E, S, W) in points
            @param spacing: the spacing between cards, tuple (H, V) in points
        """

        if spacing is None:
            spacing = (18, 18)
        elif not isinstance(spacing, (tuple, list)):
            spacing = (spacing, spacing)

        if margins is None:
            margins = self.compute_margins(pagesize, cardsize, spacing)
        elif not isinstance(margins, (tuple, list)):
            margins = (margins, margins, margins, margins)

        pages = self.page_layouts(pagesize, cardsize, margins, spacing)

        # TODO compute cards per page

        BaseDocTemplate.__init__(self,
                                 None,
                                 pagesize = pagesize,
                                 pageTemplates = pages,
                                 topMargin = margins[0],
                                 rightMargin = margins[1],
                                 bottomMargin = margins[2],
                                 leftMargin = margins[3],
                                 )

    # -------------------------------------------------------------------------
    def number_of_cards(self, pagesize, cardsize, margins, spacing):
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
            TODO docstring
            TODO validate + improve
        """

        number_of_cards = self.number_of_cards
        numh = number_of_cards(pagesize[0], cardsize[0], (18, 18), spacing[0])
        numv = number_of_cards(pagesize[1], cardsize[1], (12, 12), spacing[1])

        wh = (numh - 1) * (cardsize[0] + spacing[0]) + cardsize[0]
        wv = (numv - 1) * (cardsize[1] + spacing[1]) + cardsize[1]

        mh = (pagesize[0] - wh) / 2
        mv = (pagesize[1] - wv) / 2

        return (mv, mh, mv, mh)

    # -------------------------------------------------------------------------
    def page_layouts(self, pagesize, cardsize, margins, spacing):
        """
            TODO implement this

            Create a set of page layouts ["Front", "Back"]

        """

        pagewidth, pageheight = pagesize
        cardwidth, cardheight = cardsize

        number_of_cards = self.number_of_cards

        cards_per_row = number_of_cards(pagewidth, cardwidth, (margins[1], margins[3]), spacing[0])
        self.cards_per_row = cards_per_row

        rows_per_page = number_of_cards(pageheight, cardheight, (margins[0], margins[2]), spacing[1])
        self.rows_per_page = rows_per_page

        topmargin, leftmargin = margins[0], margins[3]

        hspacing, vspacing = spacing

        y0 = pageheight - topmargin - cardheight

        fframes = []
        fx0 = leftmargin

        bframes = []
        bx0 = pagewidth - leftmargin - cardwidth # + hshift

        for i in range(rows_per_page):

            y = y0 - i * (vspacing + cardheight)

            for j in range(cards_per_row):

                # Front
                fframes.append(Frame(fx0 + j * (cardwidth + hspacing),
                                     y,
                                     cardwidth,
                                     cardheight,
                                     leftPadding = 0,
                                     bottomPadding = 0,
                                     rightPadding = 0,
                                     topPadding = 0,
                                     ))

                # Back
                bframes.append(Frame(bx0 - j * (cardwidth + hspacing),
                                     y,
                                     cardwidth,
                                     cardheight,
                                     leftPadding = 0,
                                     bottomPadding = 0,
                                     rightPadding = 0,
                                     topPadding = 0,
                                     ))

        return [PageTemplate(id="Front",
                             frames = fframes,
                             ),
                PageTemplate(id="Back",
                             frames = bframes,
                             ),
                ]

# =============================================================================
class S3IDCardFlowable(Flowable):
    """
        Flowable-class for ID Cards (one side)
    """

    def __init__(self, item, labels=None, backside=False):
        """
            Constructor

            @param item: the data item
            @param labels: the field labels
            @param backside: this instance should render a card backside

            TODO add parameter to indicate whether there are multiple
                 cards on a page
        """

        self.item = item

        if labels is None:
            self.labels = {}
        else:
            self.labels = labels

        self.canv = None
        self.x = 0
        self.y = 0

        self.backside = backside

        # TODO call super-constructor

    # -------------------------------------------------------------------------
    def drawOn(self, canvas, x, y, **attr):
        """
            Prepare and render this flowable

            @param canvas: the canvas
            @param x: the origin of the frame (from left of page)
            @param y: the origin of the frame (from bottom of page)

            TODO fix parameter list to match prototype
        """

        # Remember canvas and position
        self.canv = canvas
        self.x = x
        self.y = y

        # Call draw
        self.draw()

    # -------------------------------------------------------------------------
    def draw(self):
        """
            Draw this flowable (called by drawOn)

            TODO: implement this
        """

        c = self.canv
        if c is None:
            return

        x = self.x
        y = self.y

        cardsize = self.cardsize
        w = cardsize[0]
        h = cardsize[1]

        # TODO Remove this
        self.draw_outline(x, y, w, h)

        x = x + w / 2
        y = y + h / 2

        c.setFont("Helvetica", 12)
        c.drawCentredString(x, y, "Back" if self.backside else "Front")

        # TODO render item.id if it has one

    # -------------------------------------------------------------------------
    def draw_outline(self, x, y, w, h, on=1, off=2):
        """
            TODO docstring
        """

        c = self.canv

        c.setLineWidth(1)
        c.setDash(on, off)
        c.lines([[x, y, x + w, y],
                 [x + w, y, x + w, y + h],
                 [x + w, y + h, x, y + h],
                 [x, y + h, x, y],
                 ])

    # -------------------------------------------------------------------------
    def wrap(self, availWidth, availHeight):
        """
            Predict the width/height of this flowable, called by rendering
            process (before drawOn)

            @param availWidth: the available width in the current frame
            @param availHeight: the available height in the current frame

            @returns: the width/height of the flowable
        """

        # Remember the frame dimensions
        # TODO initialize in constructor
        self.cardsize = (availWidth, availHeight)

        # ID card flowables use up the entire frame
        return (availWidth, availHeight)

    # -------------------------------------------------------------------------
    def split(self, availWidth, availHeight):
        """
            Split this flowable across frames, called by rendering process
            if the predicted size of the flowable exceeds the size of the
            current frame

            @param availWidth: the available width in the current frame
            @param availHeight: the available height in the current frame

            @returns: a list of flowables for the next frame
        """

        # ID card flowables do not split
        return []

# END =========================================================================
