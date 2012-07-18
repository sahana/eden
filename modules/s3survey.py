# -*- coding: utf-8 -*-

"""  Custom UI Widgets used by the survey application

    @copyright: 2011-2012 (c) Sahana Software Foundation
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

import sys

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.sqlhtml import *

from s3chart import S3Chart

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3Survey: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class LayoutBlocks():
    """
        Class that hold details of the layout blocks.
        
        This is used when resizing the layout to make the final layout uniform.
    """
    class RowBlocks():
        """
            Class the holds blocks that belong on the same row
        """
        def __init__(self, block):
            self.blocks = [block]
            self.startRow = block.startPosn[0]
            self.maxHeight = block.endPosn[0]
            self.maxWidth = block.endPosn[1]
            self.cnt = 1

        def add(self, block):
            self.blocks.append(block)
            if block.endPosn[0] > self.maxHeight:
                self.maxHeight = block.endPosn[0]
            if block.endPosn[1] > self.maxWidth:
                self.maxWidth = block.endPosn[1]
            self.cnt += 1
        # end of class RowBlocks

    def __init__(self):
        self.startPosn = [0,0]
        self.endPosn = [0,0]
        self.contains = []
        self.temp = []
        self.widgetList = []
        self.growToWidth = 0
        self.growToHeight = 0

    def growTo (self, width=None, height=None):
        if width != None:
            self.growToWidth = width
        if height != None:
            self.growToHeight = height

    def growBy(self, width=None, height=None):
        if width != None:
            self.growToWidth = self.endPosn[1] + width
        if height != None:
            self.growToHeight = self.endPosn[0] + height

    def setPosn(self, start, end):
        if self.startPosn[0] == 0 \
        or start[0] < self.startPosn[0]:
            self.startPosn[0] = start[0]
        if self.startPosn[1] == 0 \
        or start[1] > self.startPosn[1]:
            self.startPosn[1] = start[1]
        if end[0] > self.endPosn[0]:
            self.endPosn[0] = end[0]
        if end[1] > self.endPosn[1]:
            self.endPosn[1] = end[1]
        self.growToWidth = self.endPosn[1]
        self.growToHeight = self.endPosn[0]

    def slideHorizontally(self, colAdjust):
        self.startPosn[1] += colAdjust
        self.endPosn[1] += colAdjust
        for block in self.contains:
            block.slideHorizontally(colAdjust)

    def setWidgets(self, widgets):
        rowList = {}
        colList = {}
        for widget in widgets:
            startCol = widget.startPosn[1]
            startRow = widget.startPosn[0]
            if startCol in colList:
                colList[startCol] += 1
            else:
                colList[startCol] = 1
            if startRow in rowList:
                rowList[startRow] += 1
            else:
                rowList[startRow] = 1
        if len(colList) > 1:
            self.action = "columns"
        else:
            self.action = "rows"  
        self.widgetList = widgets

    def widthShortfall(self):
        return self.growToWidth - self.endPosn[1]

    def heightShortfall(self):
        return self.growToHeight - self.endPosn[0]

    def addBlock(self, start, end, widgets=[]):
        lb = LayoutBlocks()
        lb.setPosn(start, end)
        lb.setWidgets(widgets)
        length = len(self.contains)
        temp = []
        if length > 0 and self.contains[length-1].startPosn == start:
            lb.contains.append(self.contains.pop())
        for element in self.temp:
            if element.startPosn[0] < start[0] or element.startPosn[1] < start[1]:
                temp.append(element)
            else:
                lb.contains.append(element)
        self.temp = []
        for element in temp:
            self.temp.append(element)
        if self.temp != []:
            self.temp.append(lb)
        else:
            self.contains.append(lb)

    def addTempBlock(self, start, end, widgets):
        lb = LayoutBlocks()
        lb.setPosn(start, end)
        lb.setWidgets(widgets)
        self.temp.append(lb)

    def __repr__(self):
        indent = ""
        data = self.display(indent)
        return data

    def display(self, indent):
        widgets = ""
        for widget in self.widgetList:
            widgets += "%s " % widget.question.code
        data = "%s%s, %s grow to [%s, %s]- %s\n" %(indent,
                                                   self.startPosn,
                                                   self.endPosn,
                                                   self.growToHeight,
                                                   self.growToWidth,
                                                   widgets
                                                   )
        indent = indent + "  "
        for lb in self.contains:
            data += lb.display(indent)
        return data

    def align(self):
        """
            Method to align the widgets up with each other.
            
            This means that blocks that are adjacent to each other will be
            spaced to ensure that they have the same height. And blocks on top
            of each other will have the same width. 
        """
        formWidth = self.endPosn[1]
        self.realign(formWidth)

    def realign(self, formWidth):
        """
            recursive method to ensure all widgets line up
        """
        rowList = {}
        # Put all of the blocks into rows 
        for block in self.contains:
            startRow = block.startPosn[0]
            endRow = block.endPosn[0]
            # Exact match
            if startRow in rowList:
                rowList[startRow].add(block)
                continue
            # look for an overlap
            else:
                overlap = False
                for storedBlock in rowList.values():
                    if (startRow < storedBlock.startRow \
                        and endRow >= storedBlock.startRow) \
                    or (startRow < storedBlock.maxHeight \
                        and endRow >= storedBlock.maxHeight) \
                    or (startRow > storedBlock.startRow) \
                        and (endRow <= storedBlock.maxHeight):
                        storedBlock.add(block)
                        overlap = True
                        break
                if overlap:
                    continue
            # no overlap
            rowList[startRow] = self.RowBlocks(block)
        # Now set up the grow to sizes for each block
        for row in rowList.values():
            # if their is only one row then
            # it just needs to expand to fill the form width
            if row.cnt == 1:
                row.blocks[0].growTo(formWidth)
            # The amount that each block needs to expand to reach the form width
            # needs to be calculated by sharing the shortfall between each block
            # and if any block needs to grow vertically this needs to be added
            # additionally the start position my need adjusting
            else:
                widthShortfall = formWidth - row.maxWidth
                widthShortfallPart = widthShortfall / row.cnt
                colAdjust = 0
                for block in row.blocks:
                    if widthShortfall > 0:
                        widthShortfall -= widthShortfallPart
                        block.slideHorizontally(colAdjust)
                        block.growBy(widthShortfallPart)
                        colAdjust += widthShortfallPart
                    if block.endPosn[0] < row.maxHeight:
                        block.growTo(height = row.maxHeight)
                colAdjust = 0
                for block in row.blocks:
                    if widthShortfall == 0:
                        break
                    block.growBy()
                    widthShortfall -= 1
                    block.slideHorizontally(colAdjust)
                    colAdjust += 1
                rowCnt = len(row.blocks)
                if rowCnt > 1:
                    rowCntList = {}
                    for block in row.blocks:
                        rowCntList[block.startPosn[0]] = True
                    if len(rowCntList) == 1:
                        formWidth = self.growToWidth
        # The growto parameters have been set. Now grow any widgets
        # @todo: add modulo tests for blkCnt to cater for uneven results
        blkCnt = len(self.contains)
        for block in self.contains:
            if block.widgetList == []:
                block.realign(self.growToWidth)
            else:
                self.alignBlock(block, blkCnt)

    def alignBlock(self, block, blkCnt):
        if block.action == "rows":
            widthShortfall = block.widthShortfall()
            self.alignRow(block, widthShortfall)
        else:
            heightShortfall = block.heightShortfall()
            widthShortfall = block.widthShortfall()
            self.alignCol(block, heightShortfall, widthShortfall)

    def alignRow(self, block, widthShortfall):
        """
            method to align the widgets laid out in a single row.
            
            The horizontal spacing will be fixed. Identify all widgets 
            that can grow horizontally and let them do so. If their are
            multiple widgets that can grow then they will all grow by the
            same amount.
            
            Any space that is left over will be added to a margin between
            the widgets
        """
        canGrowCount = 0
        for widget in block.widgetList:
            if widget.canGrowHorizontal():
                canGrowCount += 1
        if canGrowCount > 0:
            growBy = widthShortfall / canGrowCount
            if growBy > 0:
                for widget in block.widgetList:
                    if widget.canGrowHorizontal():
                        widget.growHorizontal(growBy)
                        widthShortfall -= growBy
        # Add any unallocated space as margins between the widgets
        if widthShortfall > 0:
            marginGrow = widthShortfall / len(block.widgetList)
            if marginGrow > 0:
                for widget in block.widgetList:
                    widget.addToHorizontalMargin(marginGrow)
                    widthShortfall -= marginGrow
        if widthShortfall > 0:
            for widget in block.widgetList:
                widget.addToHorizontalMargin(1)
                widthShortfall -= 1
                if widthShortfall == 0:
                    break
        # Now sort out any vertical shortfall
        for widget in block.widgetList:
            widgetHeight = block.startPosn[0] + widget.getMatrixSize()[0]
            heightShortfall = block.growToHeight - widgetHeight
            if heightShortfall > 0:
                if widget.canGrowVertical():
                    widget.growVertical(heightShortfall)
                else:
                    widget.addToVerticalMargin(heightShortfall)

    def alignCol(self, block, heightShortfall, widthShortfall):
        """
            method to align the widgets laid out different rows
        """
        # Stretch the columns to fill the maximum width
        for widget in block.widgetList:
            widgetWidth = block.startPosn[1] + widget.getMatrixSize()[1]
            widthShortfall = block.growToWidth - widgetWidth
            # Now grow the columns to align evenly
            if widthShortfall == 0:
                continue
            if widget.canGrowHorizontal():
                widget.growHorizontal(widthShortfall)
            else:
                widget.addToHorizontalMargin(widthShortfall)
        # Now grow the rows to align evenly
        if heightShortfall == 0:
            return
        # See if the widgets can grow
        canGrowCount = 0
        for widget in block.widgetList:
            if widget.canGrowVertical():
                canGrowCount += 1
        if canGrowCount > 0:
            growBy = heightShortfall / canGrowCount
            if growBy > 0:
                for widget in block.widgetList:
                    if widget.canGrowVertical():
                        widget.growVertical(growBy)
                        heightShortfall -= growBy
        # Add any unallocated space as margins between the widgets
        if heightShortfall > 0:
            marginGrow = heightShortfall / len(block.widgetList)
            if marginGrow > 0:
                for widget in block.widgetList:
                    widget.addToVerticalMargin(marginGrow)
                    heightShortfall -= marginGrow
        if heightShortfall > 0:
            for widget in block.widgetList:
                widget.addToVerticalMargin(1)
                heightShortfall -= 1
                if heightShortfall == 0:
                    break

# =============================================================================
class DataMatrix():
    """
        Class that sets the data up ready for export to a specific format,
        such as a spreadsheet or a PDF document.

        It holds the data in a matrix with each element holding details on:
         * A unique position
         * The actual text to be displayed
         * Any style to be applied to the data
    """
    def __init__(self):
        self.matrix = {}
        self.lastRow = 0
        self.lastCol = 0
        self.fixedWidthRepr = False
        self.fixedWidthReprLen = 1

    def __repr__(self):
        repr = ""
        for row in range(self.lastRow+1):
            for col in range(self.lastCol+1):
                posn = MatrixElement.getPosn(row,col)
                if posn in self.matrix:
                    cell = self.matrix[posn]
                    data = str(cell)
                else:
                    cell = None
                    data = "-"
                if self.fixedWidthRepr:
                    xposn = 0
                    if cell != None:
                        if cell.joinedWith != None:
                            parentPosn = cell.joinedWith
                            (prow,pcol) = parentPosn.split(",")
                            xposn = col - int(pcol)
                            data = str(self.matrix[parentPosn])
                        if xposn >= len(data):
                            data = "*"
                    if len(data) > self.fixedWidthReprLen:
                        data = data[xposn:xposn+self.fixedWidthReprLen]
                    else:
                        data = data + " " * (self.fixedWidthReprLen - len(data))
                repr += data
            repr += "\n"
        return repr

    def addCell(self, row, col, data, style, horizontal=0, vertical=0):
        cell = MatrixElement(row,col,data, style)
        if horizontal !=0 or vertical!=0:
            cell.merge(horizontal, vertical)
        try:
            self.addElement(cell)
        except Exception as msg:
            print >> sys.stderr, msg
        return (row + 1 + vertical,
                col + 1 + horizontal)

    def addElement(self, element):
        """
            Add an element to the matrix, checking that the position is unique.
        """
        posn = element.posn()
        if posn in self.matrix:
            msg = "Attempting to add data %s at posn %s. This is already taken with data %s" % \
                        (element, posn, self.matrix[posn])
            raise Exception(msg)
        self.matrix[posn] = element
        element.parents.append(self)
        if element.merged():
            self.joinElements(element)
        if element.row + element.mergeV > self.lastRow:
            self.lastRow = element.row + element.mergeV
        if element.col + element.mergeH > self.lastCol:
            self.lastCol = element.col + element.mergeH

    def joinedElementStyles(self, rootElement):
        """
            return a list of all the styles used by all the elements joined
            to the root element
        """
        styleList = []
        row = rootElement.row
        col = rootElement.col
        for v in range(rootElement.mergeV + 1):
            for h in range(rootElement.mergeH + 1):
                newPosn = "%s,%s" % (row + v, col + h)
                styleList += self.matrix[newPosn].styleList
        return styleList

    def joinElements(self, rootElement):
        """
            This will set the joinedWith property to the posn of rootElement
            for all the elements that rootElement joins with to make a single
            large merged element.
        """
        row = rootElement.row
        col = rootElement.col
        posn = rootElement.posn()
        for v in range(rootElement.mergeV + 1):
            for h in range(rootElement.mergeH + 1):
                newPosn = "%s,%s" % (row + v, col + h)
                if newPosn == posn:
                    continue
                if newPosn in self.matrix:
                    if self.matrix[newPosn].joinedWith == posn:
                        continue
                    msg = "Attempting to merge element at posn %s. The following data will be lost %s" % \
                                (newPosn, self.matrix[newPosn])
                    self.matrix[newPosn].joinedWith = posn
                else:
                    childElement = MatrixElement(row, col, "", [])
                    childElement.joinedWith = posn
                    self.matrix[newPosn] = childElement

    def boxRange(self, startrow, startcol, endrow, endcol, width=1):
        """
            Function to add a bounding box around the elements contained by
            the elements (startrow, startcol) and (endrow, endcol)

            This uses standard style names:
            boxL, boxB, boxR, boxT
            for Left, Bottom, Right and Top borders respectively
        """
        for r in range(startrow, endrow):
            posn = "%s,%s" % (r, startcol)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxL%s"%width)
            else:
                self.addElement(MatrixElement(r, startcol, "", "boxL%s"%width))
            posn = "%s,%s" % (r, endcol)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxR%s"%width)
            else:
                self.addElement(MatrixElement(r, endcol, "", "boxR%s"%width))
        for c in range(startcol, endcol + 1):
            posn = "%s,%s" % (startrow, c)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxT%s"%width)
            else:
                self.addElement(MatrixElement(startrow, c, "", "boxT%s"%width))
            posn = "%s,%s" % (endrow - 1, c)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxB%s"%width)
            else:
                self.addElement(MatrixElement(endrow - 1, c, "", "boxB%s"%width))

# =============================================================================
class MatrixElement():
    """
        Class that holds the details of a single element in the matrix

        * posn - row & col
        * text - the actual data that will be displayed at the given position
        * style - a list of styles that will be applied to this location
    """
    def __init__(self, row, col, data, style):
        self.row = row
        self.col = col
        self.text = data
        self.mergeH = 0
        self.mergeV = 0
        self.joinedWith = None
        self.parents = []
        if isinstance(style, list):
            self.styleList = style
        else:
            self.styleList = [style]

    def __repr__(self):
        return self.text

    def merge(self, horizontal=0, vertical=0):
        self.mergeH = horizontal
        self.mergeV = vertical
        for parent in self.parents:
            parent.joinElements(self)

    @staticmethod
    def getPosn(row, col):
        """ Standard representation of the position """
        return "%s,%s" % (row, col)

    def posn(self):
        """ Standard representation of the position """
        return self.getPosn(self.row, self.col)

    def nextX(self):
        return self.row + self.mergeH + 1

    def nextY(self):
        return self.col + self.mergeV + 1

    def merged(self):
        if self.mergeH > 0 or self.mergeV > 0:
            return True
        return False

    def joined(self):
        if self.joinedWith == None:
            return False
        else:
            return True

# =============================================================================
class DataMatrixBuilder():
    def __init__(self,
                 primaryMatrix,
                 layout=None,
                 widgetList = [],
                 secondaryMatrix=None,
                 langDict = None,
                 addMethod=None
                ):
        self.matrix = primaryMatrix
        self.layout = layout
        self.widgetList = widgetList
        self.widgetsInList = []
        self.answerMatrix = secondaryMatrix
        self.langDict = langDict
        if addMethod == None:
            self.addMethod = self.addData
        else:
            self.addMethod = addMethod
        self.labelLeft = None
        self.boxOpen = False
        self.postponeLayoutUpdate = False

    def processRule(self, rules, row, col, matrix):
        startcol = col
        startrow = row
        endcol = col
        endrow = row
        action="rows"
        self.widgetsInList = []
        for element in rules:
            row = endrow
            col = startcol
            self.nextrow = row
            self.nextcol = col
            if isinstance(element,list):
                (endrow, endcol) = self.processList(element, row, col, matrix, action)
            elif isinstance(element,dict):
                (endrow, endcol) = self.processDict(element, rules, row, col, matrix, action)
            if self.layout != None:
                if self.widgetsInList == []:
                    self.layout.addBlock((row, col), (endrow, endcol))
                else:
                    self.layout.addTempBlock((row, col), (endrow, endcol), self.widgetsInList)
                    self.widgetsInList = []
        return (endrow, endcol)

    def processList(self, rules, row, col, matrix, action="rows"):
        startcol = col
        startrow = row
        endcol = col
        endrow = row
        for element in rules:
            if action == "rows":
                row = startrow
                col = endcol
            elif action == "columns":
                row = endrow
                col = startcol
            # If the rule is a list then step through each element
            if isinstance(element,list):
                (endrow, endcol) = self.processList(element, row, col, matrix, action)
            elif isinstance(element,dict):
                (endrow, endcol) = self.processDict(element, rules, row, col, matrix, action)
            else:
                (endrow, endcol) = self.addMethod(self, element, row, col)
            if endrow > self.nextrow:
                self.nextrow = endrow
            if endcol > self.nextcol:
                self.nextcol = endcol
        self.addToLayout(startrow, startcol)
        return (self.nextrow, self.nextcol)

    def processDict(self, rules, parent, row, col, matrix, action="rows"):
        startcol = col
        startrow = row
        endcol = col
        endrow = row
        if "boxOpen" in rules:
            return self.processBox(rules, row, col, matrix, action)
        if "heading" in rules:
            text = rules["heading"]
            if len(parent) == 1:
                width = min(len(text),matrix.lastCol)+1
                height = 1
                styleName = "styleSectionHeading"
            else:
                width = 11
                height = len(text)/(2*width) + 1
                styleName = "styleSubHeader"
            cell = MatrixElement(row, col, text, style = styleName)
            cell.merge(horizontal = width-1, vertical = height-1)
            try:
                matrix.addElement(cell)
            except Exception as msg:
                print >> sys.stderr, msg
                return (row,col)
            endrow = row + height
            endcol = col + width
            if "hint" in rules:
                text = rules["hint"]
                cell = MatrixElement(endrow,startcol,text, style="styleHint")
                height = int(((len(text)/(2*width))*0.75)+0.5) + 1
                cell.merge(horizontal=width-1, vertical=height-1)
                try:
                    matrix.addElement(cell)
                except Exception as msg:
                    print >> sys.stderr, msg
                    return (row,col)
                endrow = endrow + height
        if "labelLeft" in rules:
            self.labelLeft = rules["labelLeft"]
        if "columns" in rules:
            value = rules["columns"]
            maxrow = startrow
            for rules in value:
                row = startrow
                self.nextrow = startrow
                col = endcol
                if isinstance(rules,list):
                    (endrow, endcol) = self.processList(rules, row, col, matrix, "columns")
                elif isinstance(rules,dict):
                    (endrow, endcol) = self.processDict(rules, value, row, col, matrix, "columns")
                if endrow > maxrow:
                    maxrow = endrow
                if endcol > self.nextcol:
                    self.nextcol = endcol
            self.nextrow = maxrow
            endrow = self.nextrow
            endcol = self.nextcol
        return (endrow, endcol)

    def processBox(self, rules, row, col, matrix, action="rows"):
        startcol = col
        startrow = row
        endcol = col
        endrow = row
        headingrow = row
        self.addToLayout(startrow, startcol, andThenPostpone = True)
        if "heading" in rules:
            row += 1
        if "data" in rules:
            self.boxOpen = True
            value = rules["data"]
            (endrow, endcol) = self.processList(value, row, col, matrix, action)
            self.boxOpen = False
        if "heading" in rules:
            value = rules["heading"]
            (row, endcol) = self.addLabel(value, headingrow, col, endcol - col, 1)
        self.matrix.boxRange(startrow, startcol, endrow, endcol-1)
        self.addToLayout(startrow, startcol, endPostpone = True)
        return (endrow, endcol)

    def addToLayout(self, startrow, startcol, andThenPostpone = None, endPostpone = None):
        if endPostpone != None:
            self.postponeLayoutUpdate = not endPostpone
        if not self.postponeLayoutUpdate \
        and self.layout != None \
        and (startrow != self.nextrow or startcol != self.nextcol):
            if self.widgetsInList != []:
                self.layout.addTempBlock((startrow, startcol), (self.nextrow, self.nextcol), self.widgetsInList)
                self.widgetsInList = []
        if andThenPostpone != None:
            self.postponeLayoutUpdate = andThenPostpone

    def addArea(self, element, row, col):
        try:
            widgetObj = self.widgetList[element]
        except:
            _debug("Unable to find element %s in the template" % element)
            return self.matrix.addCell(row, col, "", [])
        widgetObj.startPosn = (col, row)
        if self.labelLeft:
            widgetObj.labelLeft = (self.labelLeft == "True")
            self.labelLeft = None
        self.widgetsInList.append(widgetObj)
        (vert, horiz) = widgetObj.getMatrixSize()
        return self.matrix.addCell(row,
                                   col,
                                   element,
                                   [],
                                   horizontal=horiz-1,
                                   vertical=vert-1,
                                  )

    def addLabel(self, label, row, col, width=11, height=None, style="styleSubHeader"):
        cell = MatrixElement(row,col,label, style=style)
        if height == None:
            height = len(label)/(2*width) + 1
        cell.merge(horizontal=width-1, vertical=height-1)
        try:
            self.matrix.addElement(cell)
        except Exception as msg:
            print >> sys.stdout,  msg
            return (row,col)
        endrow = row + height
        endcol = col + width
        return (endrow, endcol)

    def addData(self, element, row, col):
        try:
            widgetObj = self.widgetList[element]
        except:
            _debug("Unable to find element %s in the template" % element)
            return self.matrix.addCell(row, col, "", [])
        widgetObj.startPosn = (col, row)
        self.widgetsInList.append(widgetObj)
        if self.labelLeft:
            widgetObj.labelLeft = (self.labelLeft == "True")
            self.labelLeft = None
        try:
            (endrow, endcol) = widgetObj.writeToMatrix(self.matrix,
                                                       row,
                                                       col,
                                                       answerMatrix=self.answerMatrix,
                                                       langDict = self.langDict
                                                      )
        except Exception as msg:
            print >> sys.stderr, msg
            return (row,col)
        #if question["type"] == "Grid":
        if self.boxOpen == False:
            self.matrix.boxRange(row, col, endrow, endcol-1)
        return (endrow, endcol)

# =============================================================================
def getMatrix(title,
              logo,
              series,
              layout,
              widgetList,
              secondaryMatrix,
              langDict,
              showSectionLabels=True,
              layoutBlocks=None):
    matrix = DataMatrix()
    if secondaryMatrix:
        secondaryMatrix = DataMatrix()
    else:
        secondaryMatrix = None
    matrix.fixedWidthRepr = True
    if layoutBlocks == None:
        addMethod = DataMatrixBuilder.addData
    else:
        addMethod = DataMatrixBuilder.addArea
    builder = DataMatrixBuilder(matrix,
                                layoutBlocks,
                                widgetList,
                                secondaryMatrix = secondaryMatrix,
                                langDict = langDict,
                                addMethod=addMethod
                                )
    row = 2
    for (section, rules) in layout:
        col = 0
        if showSectionLabels:
            row += 1
            (row,nextCol) = matrix.addCell(row,
                                           col,
                                           section,
                                           ["styleHeader"],
                                           len(section)
                                          )
        (row, col) = builder.processRule(rules, row, col, matrix)
    row = 0
    col = 0
    logoWidth = 0
    if logo != None:
        logoWidth = 6
        (nextRow,col) = matrix.addCell(row,col,"",[],logoWidth-1,1)
    titleWidth = max(len(title), matrix.lastCol-logoWidth)
    (row,col) = matrix.addCell(row,col,title,["styleTitle"],titleWidth,1)
    if layoutBlocks != None:
        maxCol = col
        for block in layoutBlocks.contains:
            if block.endPosn[1] > maxCol:
                maxCol = block.endPosn[1]
        layoutBlocks.setPosn((0,0), (row,maxCol))
    matrix.boxRange(0, 0, matrix.lastRow+1, matrix.lastCol, 2)
    if secondaryMatrix:
        return (matrix, secondaryMatrix)
    else:
        return matrix

# =============================================================================
# Question Types
def survey_stringType(question_id = None):
    return S3QuestionTypeStringWidget(question_id)
def survey_textType(question_id = None):
    return S3QuestionTypeTextWidget(question_id)
def survey_numericType(question_id = None):
    return S3QuestionTypeNumericWidget(question_id)
def survey_dateType(question_id = None):
    return S3QuestionTypeDateWidget(question_id)
def survey_timeType(question_id = None):
    return S3QuestionTypeTimeWidget(question_id)
def survey_optionType(question_id = None):
    return S3QuestionTypeOptionWidget(question_id)
def survey_ynType(question_id = None):
    return S3QuestionTypeOptionYNWidget(question_id)
def survey_yndType(question_id = None):
    return S3QuestionTypeOptionYNDWidget(question_id)
def survey_optionOtherType(question_id = None):
    return S3QuestionTypeOptionOtherWidget(question_id)
def survey_multiOptionType(question_id = None):
    return S3QuestionTypeMultiOptionWidget(question_id)
def survey_locationType(question_id = None):
    return S3QuestionTypeLocationWidget(question_id)
def survey_linkType(question_id = None):
    return S3QuestionTypeLinkWidget(question_id)
def survey_ratingType(question_id = None):
    pass
def survey_gridType(question_id = None):
    return S3QuestionTypeGridWidget(question_id)
def survey_gridChildType(question_id = None):
    return S3QuestionTypeGridChildWidget(question_id)
def survey_T(phrase, langDict):
    """
        Function to translate a phrase using the dictionary passed in
    """
    if phrase in langDict and langDict[phrase] != "":
        return langDict[phrase]
    else:
        return phrase

survey_question_type = {
    "String": survey_stringType,
    "Text": survey_textType,
    "Numeric": survey_numericType,
    "Date": survey_dateType,
    "Time": survey_timeType,
    "Option": survey_optionType,
    "YesNo": survey_ynType,
    "YesNoDontKnow": survey_yndType,
    "OptionOther": survey_optionOtherType,
    "MultiOption" : survey_multiOptionType,
    "Location": survey_locationType,
    "Link" : survey_linkType,
    #"Rating": survey_ratingType,
    "Grid" : survey_gridType,
    "GridChild" : survey_gridChildType,
}

# =============================================================================
class S3QuestionTypeAbstractWidget(FormWidget):
    """
        Abstract Question Type widget

        A QuestionTypeWidget can have three basic states:

        The first is as a descriptor for the type of question.
        In this state it will hold the information about what this type of
        question may look like.

        The second state is when it is associated with an actual question
        on the database. Then it will additionally hold information about what
        this actual question looks like.

        The third state is when the widget of an actual question is
        associated with a single answer to that question. If that happens then
        the self.question record from the database is extended to hold
        the actual answer and the complete_id of that answer.

        For example: A numeric question type has a metadata value of "Format"
        this can be used to describe how the data could be formatted to
        represent a number. When this question type is associated with an
        actual numeric question then the metadata might be "Format" : n, which
        would mean that it is an integer value.

        The general instance variables:

        @ivar metalist: A list of all the valid metadata descriptors. This would
                        be used by a UI when designing a question
        @ivar attr: Any HTML/CSS attributes passed in by the call to display
        @ivar webwidget: The web2py widget that should be used to display the
                         question type
        @ivar typeDescription: The description of the type when it is displayed
                               on the screen such as in reports

        The instance variables when the widget is associated with a question:

        @ivar id: The id of the question from the survey_question table
        @ivar question: The question record from the database.
                        Note this variable can be extended to include the
                        answer taken from the complete_id, allowing the
                        question to hold a single answer. This is needed when
                        updating responses.
        @ivar qstn_metadata: The actual metadata for this question taken from
                             the survey_question_metadata table and then
                             stored as a descriptor value pair
        @ivar field: The field object from metadata table, which can be used
                     by the widget to add additional rules (such as a requires)
                     before setting up the UI when inputing data

        @author: Graeme Foster (graeme at acm dot org)

    """

    def __init__(self,
                 question_id
                ):

        self.ANSWER_VALID = 0
        self.ANSWER_MISSING = 1
        self.ANSWER_PARTLY_VALID = 2
        self.ANSWER_INVALID = 3

        T = current.T
        s3db = current.s3db
        # The various database tables that the widget may want access to
        self.qtable = s3db.survey_question
        self.mtable = s3db.survey_question_metadata
        self.qltable = s3db.survey_question_list
        self.ctable = s3db.survey_complete
        self.atable = s3db.survey_answer
        # the general instance variables
        self.metalist = ["Help message"]
        self.attr = {}
        self.webwidget = StringWidget
        self.typeDescription = None
        self.startPosn = (0,0)
        self.xlsWidgetSize = (6,0)
        self.xlsMargin = [0,0]
        self.langDict = dict()
        self.label = True
        self.labelLeft = True
        # The instance variables when the widget is associated with a question
        self.id = question_id
        self.question = None
        self.qstn_metadata = {}
        # Initialise the metadata from the question_id
        self._store_metadata()
        self.field = self.mtable.value

        try:
            from xlwt.Utils import rowcol_to_cell
            self.rowcol_to_cell = rowcol_to_cell
        except:
            import sys
            print >> sys.stderr, "WARNING: S3Survey: xlwt module needed for XLS export"

    # -------------------------------------------------------------------------
    def setDict(self, langDict):
        self.langDict = langDict

    # -------------------------------------------------------------------------
    def _store_metadata(self, qstn_id=None, update=False):
        """
            This will store the question id in self.id,
            the question data in self.question, and
            the metadata for this specific question in self.qstn_metadata

            It will only get the data from the db if it hasn't already been
            retrieved, or if the update flag is True
        """
        if qstn_id != None:
            if self.id != qstn_id:
                self.id = qstn_id
                # The id has changed so force an update
                update = True
        if self.id == None:
            self.question = None
            self.qstn_metadata = {}
            return
        if self.question == None or update:
            db = current.db
            s3 = current.response.s3
            # Get the question from the database
            query = (self.qtable.id == self.id)
            self.question = db(query).select(limitby=(0, 1)).first()
            if self.question == None:
                raise Exception("no question with id %s in database" % self.id)
            # Get the metadata from the database and store in qstn_metadata
            self.question.name = s3.survey_qstn_name_represent(self.question.name)
            query = (self.mtable.question_id == self.id)
            self.rows = db(query).select()
            for row in self.rows:
                # Remove any double quotes from around the data before storing
                self.qstn_metadata[row.descriptor] = row.value.strip('"')

    # -------------------------------------------------------------------------
    def get(self, value, default=None):
        """
            This will return a single metadata value held by the widget
        """
        if value in self.qstn_metadata:
            return self.qstn_metadata[value]
        else:
            return default

    # -------------------------------------------------------------------------
    def set(self, value, data):
        """
            This will store a single metadata value
        """
        self.qstn_metadata[value] = data


    # -------------------------------------------------------------------------
    def getAnswer(self):
        """
            Return the value of the answer for this question
        """
        if "answer" in self.question:
            answer = self.question.answer
        else:
            answer = ""
        return answer

    # -------------------------------------------------------------------------
    def repr(self, value=None):
        """
            function to format the answer, which can be passed in
        """
        if value == None:
            value = self.getAnswer()
        return value

    # -------------------------------------------------------------------------
    def loadAnswer(self, complete_id, question_id, forceDB=False):
        """
            This will return a value held by the widget
            The value can be held in different locations
            1) In the widget itself:
            2) On the database: table.survey_complete
        """
        value = None
        self._store_metadata(question_id)
        if "answer" in self.question and \
           self.question.complete_id == complete_id and \
           forceDB == False:
            answer = self.question.answer
        else:
            query = (self.atable.complete_id == complete_id) & \
                    (self.atable.question_id == question_id)
            row = current.db(query).select(limitby=(0, 1)).first()
            if row != None:
                value = row.value
                self.question["answer"] = value
            self.question["complete_id"] = complete_id
        return value

    # -------------------------------------------------------------------------
    def initDisplay(self, **attr):
        """
            This method set's up the variables that will be used by all
            display methods of fields for the question type.
            It uses the metadata to define the look of the field
        """
        if "question_id" in attr:
            self.id = attr["question_id"]
        if self.id == None:
            raise Exception("Need to specify the question_id for this QuestionType")
        qstn_id = self.id
        self._store_metadata(qstn_id)
        attr["_name"] = self.question.code
        self.attr = attr

    # -------------------------------------------------------------------------
    def display(self, **attr):
        """
            This displays the widget on a web form. It uses the layout
            function to control how the widget is displayed
        """
        self.initDisplay(**attr)
        value = self.getAnswer()
        input = self.webwidget.widget(self.field, value, **self.attr)
        return self.layout(self.question.name, input, **attr)

    # -------------------------------------------------------------------------
    def fullName(self):
        if "parentCode" in self.question:
            db = current.db
            query = db(self.qtable.code == self.question.parentCode)
            record = query.select(self.qtable.id,
                                  self.qtable.name,
                                  limitby=(0, 1)).first()
            if record != None:
                parentWidget = survey_question_type["Grid"](record.id)
                subHeading = parentWidget.getHeading(self.question.parentNumber)
                return "%s (%s)" % (self.question.name,
                                    subHeading)
        return self.question.name

    # -------------------------------------------------------------------------
    def layout(self, label, widget, **attr):
        """
            This lays the label widget that is passed in on the screen.

            Currently it has a single default layout mechanism but in the
            future it will be possible to add more which will be controlled
            vis the attr passed into display and stored in self.attr
        """
        if "display" in attr:
            display = attr["display"]
        else:
            display = "Default"
        if display == "Default":
            elements = []
            elements.append(TR(TH(label), TD(widget),
                               _class="survey_question"))
            return TAG[""](elements)
        elif display == "Control Only":
            return TD(widget)

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """
        return value

    # -------------------------------------------------------------------------
    def type_represent(self):
        """
            Display the type in a DIV for displaying on the screen
        """
        return DIV(self.typeDescription, _class="surveyWidgetType")

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid 
        """
        return "string"

    # -------------------------------------------------------------------------
    def _Tquestion(self, langDict):
        """
            Function to translate the question using the dictionary passed in
        """
        return survey_T(self.question["name"], langDict)

    # -------------------------------------------------------------------------
    def getLabelSize(self, maxWidth = 20):
        """
            function to return the size of the label, in terms of merged
            MatrixElements
        """
        labelSize = (0,0)
        if self.label:
            labelWidth = maxWidth/2
            if not self.labelLeft:
                labelWidth = self.xlsWidgetSize[0] + 1
            _TQstn = self._Tquestion(self.langDict)
            labelSize = (labelWidth, len(_TQstn)/(4 * labelWidth / 3) + 1)
        return labelSize
        
    # -------------------------------------------------------------------------
    def getWidgetSize(self, maxWidth = 20):
        """
            function to return the size of the input control, in terms of merged
            MatrixElements
        """
        return (self.xlsWidgetSize[0] + 1, self.xlsWidgetSize[1] + 1)
        
    # -------------------------------------------------------------------------
    def getMatrixSize(self):
        """
            function to return the size of the widget
        """
        labelSize = self.getLabelSize()
        widgetSize = self.getWidgetSize()
        if self.labelLeft:
            return (max(labelSize[1],widgetSize[1]) + self.xlsMargin[1],
                    labelSize[0] + widgetSize[0] + self.xlsMargin[0])
        else:
            return (labelSize[1] + widgetSize[1] + self.xlsMargin[1],
                    max(labelSize[0],widgetSize[0]) + self.xlsMargin[0])

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return False

    # -------------------------------------------------------------------------
    def canGrowVertical(self):
        return False

    # -------------------------------------------------------------------------
    def growHorizontal(self, amount):
        if self.canGrowHorizontal():
            self.xlsWidgetSize[0] += amount

    # -------------------------------------------------------------------------
    def growVertical(self, amount):
        if self.canGrowHorizontal():
            self.xlsWidgetSize[1] += amount

    # -------------------------------------------------------------------------
    def addToHorizontalMargin(self, amount):
        self.xlsMargin[0] += amount

    # -------------------------------------------------------------------------
    def addToVerticalMargin(self, amount):
        self.xlsMargin[1] += amount

    # -------------------------------------------------------------------------
    def addPaddingAroundWidget(self, matrix, startrow, startcol, lWidth, lHeight, wWidth, wHeight):
        if self.labelLeft:
            # Add padding below the input boxes
            if lHeight > wHeight:
                cellPadding = MatrixElement(startrow + wHeight,startcol + lWidth,"", style="styleText")
                cellPadding.merge(wWidth-1,lHeight - wHeight - 1)
                matrix.addElement(cellPadding)
            # Add padding below the label
            if lHeight < wHeight:
                cellPadding = MatrixElement(startrow + lHeight,startcol,"", style="styleText")
                cellPadding.merge(lWidth-1,wHeight - lHeight - 1)
                matrix.addElement(cellPadding)
                height = wHeight + 1
        else:
            # Add padding to make the widget the same width as the label
            if lWidth > wWidth:
                cellPadding = MatrixElement(startrow+lHeight,startcol+wWidth,"", style="styleText")
                cellPadding.merge(lWidth - wWidth - 1, lHeight-1)
                matrix.addElement(cellPadding)
            # Add padding to make the label the same width as the widget
            if lWidth < wWidth:
                cellPadding = MatrixElement(startrow,startcol + lWidth,"", style="styleText")
                cellPadding.merge(wWidth - lWidth - 1, wHeight-1)
                matrix.addElement(cellPadding)

    # -------------------------------------------------------------------------
    def addPaddingToCell(self,
                         matrix,
                         startrow,
                         startcol,
                         endrow,
                         endcol,
                         ):
        # Add widget padding
        if self.xlsMargin[0] > 0:
            cellPadding = MatrixElement(startrow,endcol,"", style="styleText")
            cellPadding.merge(self.xlsMargin[0]-1,endrow - startrow -1)
            matrix.addElement(cellPadding)
        if self.xlsMargin[1] > 0:
            cellPadding = MatrixElement(endrow,startcol,"", style="styleText")
            cellPadding.merge(endcol-startcol+self.xlsMargin[0]-1,self.xlsMargin[1]-1)
            matrix.addElement(cellPadding)

    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict=dict(),
                      answerMatrix=None
                      ):
        """
            Function to write out basic details to the matrix object
        """
        self._store_metadata()
        startrow = row
        startcol = col
        mergeLH = 0
        mergeLV = 0
        height = 0
        width = 0
        if self.label:
            _TQstn = self._Tquestion(langDict)
            cell = MatrixElement(row,
                                 col,
                                 _TQstn,
                                 style="styleSubHeader")
            (width, height) = self.getLabelSize()
            mergeLH = width - 1
            mergeLV = height - 1
            cell.merge(mergeLH,mergeLV)
            matrix.addElement(cell)
            if self.labelLeft:
                col += 1 + mergeLH
            else:
                row += 1 + mergeLV
        cell = MatrixElement(row,col,"", style="styleInput")
        mergeWH = self.xlsWidgetSize[0]
        mergeWV = self.xlsWidgetSize[1]
        cell.merge(mergeWH,mergeWV)
        matrix.addElement(cell)
        if self.labelLeft:
            height = max(height, mergeWV + 1)
            width += mergeWH + 1
        else:
            height += mergeWV + 1
            width = max(width, mergeWH + 1)
        self.addPaddingAroundWidget(matrix, startrow, startcol, mergeLH+1, mergeLV+1, mergeWH+1, mergeWV+1)
        # Add widget padding
        self.addPaddingToCell(matrix, startrow, startcol, startrow + height, startcol + width)
        height += self.xlsMargin[1]
        width += self.xlsMargin[0]
        # Add details to the answerMatrix (if required)
        if answerMatrix != None:
            answerRow = answerMatrix.lastRow+1
            cell = MatrixElement(answerRow, 0, self.question["code"],
                                 style="styleSubHeader")
            answerMatrix.addElement(cell)
            cell = MatrixElement(answerRow, 3,
                                 self.rowcol_to_cell(row, col),
                                 style="styleText")
            answerMatrix.addElement(cell)
        endcol = startcol+width
        endrow = startrow+height
        if DEBUG:
            # Only for debugging purposes
            self.verifyCoords(endrow, endcol)
        return (endrow, endcol)
        #if self.labelLeft:
        #    return (row+self.xlsMargin[1]+height, col+self.xlsMargin[0]+mergeWH)
        #else:
        #    return (row+self.xlsMargin[1]+mergeLV+mergeWV, col+self.xlsMargin[0]+max(mergeLH,mergeWH))

    # -------------------------------------------------------------------------
    def writeToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.
        """
        from PyRTF import Paragraph, \
                          Cell, \
                          B
        line = []
        p = Paragraph(ss.ParagraphStyles.Normal)
        p.append(B(str(self.fullName())))
        line.append(Cell(p))
        p = Paragraph(ss.ParagraphStyles.NormalGrey)
        p.append()
        line.append(Cell(p))
        return line

    # -------------------------------------------------------------------------
    def verifyCoords(self, endrow, endcol):
        (width, height) = self.getMatrixSize()
        calcrow = self.startPosn[1] + width
        calccol = self.startPosn[0] + height
        error = False
        if calcrow != endrow:
            error = True
        if calccol != endcol:
            error = True
        if error:
            w_code = self.question["code"]
            msg = "Coord Verification Error for widget %s, startPosn:(%s, %s), expected:(%s, %s), observed:(%s, %s)" % (w_code, self.startPosn[1], self.startPosn[0], endrow, endcol, calcrow, calccol)
            print >> sys.stdout, msg
    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget

            NOTE: Not currently used but will be used when the UI supports the
                  validation of data entered in to the web form
        """
        if len(valueList) == 0:
            return self.ANSWER_MISSING
        data = value(valueList, 0)
        if data == None:
            return self.ANSWER_MISSING
        length = self.get("Length")
        if length != None and length(data) > length:
            return ANSWER_PARTLY_VALID
        return self.ANSWER_VALID

    # -------------------------------------------------------------------------
    def metadata(self, **attr):
        """
            Create the input fields for the metadata for the QuestionType

            NOTE: Not currently used but will be used when the UI supports the
                  creation of the template and specifically the questions in
                  the template
        """
        if "question_id" in attr:
            self._store_metadata(attr["question_id"])
        elements = []
        for fieldname in self.metalist:
            value = self.get(fieldname, "")
            input = StringWidget.widget(self.field, value, **attr)
            elements.append(TR(TD(fieldname), TD(input)))
        return TAG[""](elements)

# =============================================================================
class S3QuestionTypeTextWidget(S3QuestionTypeAbstractWidget):
    """
        Text Question Type widget

        provides a widget for the survey module that will manage plain
        text questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """

    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.webwidget = TextWidget
        self.typeDescription = T("Long Text")
        self.xlsWidgetSize = [12,5]

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return True

    # -------------------------------------------------------------------------
    def canGrowVertical(self):
        return True

    # -------------------------------------------------------------------------
    def writeToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.
        """
        from PyRTF import Paragraph, \
                          Cell, \
                          B
        line = []
        p = Paragraph(ss.ParagraphStyles.Normal)
        p.append(B(str(self.fullName())))
        # Add some spacing to increase the text size
        p2 = Paragraph(ss.ParagraphStyles.Normal)
        line.append(Cell(p,p2,p2,p2))
        p = Paragraph(ss.ParagraphStyles.NormalGrey)
        p.append("")
        line.append(Cell(p))
        return line

# =============================================================================
class S3QuestionTypeStringWidget(S3QuestionTypeAbstractWidget):
    """
        String Question Type widget

        provides a widget for the survey module that will manage plain
        string questions (text with a limited length).

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of characters

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.metalist.append("Length")
        self.typeDescription = T("Short Text")
        self.xlsWidgetSize = [12,0]

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return True

    # -------------------------------------------------------------------------
    def display(self, **attr):
        if "length" in self.qstn_metadata:
            length = self.qstn_metadata["length"]
            attr["_size"] = length
            attr["_maxlength"] = length
        return S3QuestionTypeAbstractWidget.display(self, **attr)

# =============================================================================
class S3QuestionTypeNumericWidget(S3QuestionTypeAbstractWidget):
    """
        Numeric Question Type widget

        provides a widget for the survey module that will manage simple
        numerical questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The length if the number, default length of 10 characters
        Format:       Describes the makeup of the number, as follows:
                      n    integer
                      n.   floating point
                      n.n  floating point, the number of decimal places defined
                           by the number of n's that follow the decimal point

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.metalist.append("Length")
        self.metalist.append("Format")
        self.typeDescription = T("Numeric")

    # -------------------------------------------------------------------------
    def display(self, **attr):
        length = self.get("Length", 10)
        attr["_size"] = length
        attr["_maxlength"] = length
        return S3QuestionTypeAbstractWidget.display(self, **attr)

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """
        return str(self.formattedAnswer(value))

    # -------------------------------------------------------------------------
    def formattedAnswer(self, data, format=None):
        if format == None:
            format = self.get("Format", "n")
        parts = format.partition(".")
        try:
            result = float(data)
        except:
            result = 0
        if parts[1] == "": # No decimal point so must be a whole number
            return int(result)
        else:
            if parts[2] == "": # No decimal places specified
                return result
            else:
                return round(result, len(parts[2]))

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid 
        """
        format = self.get("Format", "n")
        if format == "n":
            return "integer"
        else:
            return "double"

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("Length", 10)
        format = self.get("Format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

# =============================================================================
class S3QuestionTypeDateWidget(S3QuestionTypeAbstractWidget):
    """
        Date Question Type widget

        provides a widget for the survey module that will manage simple
        date questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Date")

    # -------------------------------------------------------------------------
    def display(self, **attr):
        #from s3widgets import S3DateWidget
        #value = self.getAnswer()
        #widget = S3DateWidget()
        #input = widget(self.field, value, **self.attr)
        #return self.layout(self.question.name, input, **attr)
        return S3QuestionTypeAbstractWidget.display(self, **attr)

    # -------------------------------------------------------------------------
    def formattedAnswer(self, data):
        """
            This will take a string and do it's best to return a Date object
            It will try the following in order
            * Convert using the ISO format:
            * look for a month in words a 4 digit year and a day (1 or 2 digits)
            * a year and month that matches the date now and NOT a future date
            * a year that matches the current date and the previous month
        """
        rawDate = data
        date = None
        try:
            # First convert any non-numeric to a hyphen
            isoDate = ""
            addHyphen = False
            for char in rawDate:
                if char.isdigit:
                    if addHyphen == True and isoDate != "":
                        iscDate += "-"
                    isoDate += char
                    addHyphen = False
                else:
                    addHyphen = True
            # @ToDo: Use deployment_settings.get_L10n_date_format()
            date = datetime.strptime(rawDate, "%Y-%m-%d")
            return date
        except ValueError:
            try:
                for month in monthList:
                    if month in rawDate:
                        search = re,search("\D\d\d\D", rawDate)
                        if search:
                            day = search.group()
                        else:
                            search = re,search("^\d\d\D", rawDate)
                            if search:
                                day = search.group()
                            else:
                                search = re,search("\D\d\d$", rawDate)
                                if search:
                                    day = search.group()
                                else:
                                    search = re,search("\D\d\D", rawDate)
                                    if search:
                                        day = "0" + search.group()
                                    else:
                                        search = re,search("^\d\D", rawDate)
                                        if search:
                                            day = "0" + search.group()
                                        else:
                                            search = re,search("\D\d$", rawDate)
                                            if search:
                                                day = "0" + search.group()
                                            else:
                                                raise ValueError
                        search = re,search("\D\d\d\d\d\D", rawDate)
                        if search:
                            year = search.group()
                        else:
                            search = re,search("^\d\d\d\d\D", rawDate)
                            if search:
                                year = search.group()
                            else:
                                search = re,search("\D\d\d\d\d$", rawDate)
                                if search:
                                    year = search.group()
                                else:
                                    raise ValueError
                    # @ToDo: Use deployment_settings.get_L10n_date_format()
                    testDate = "%s-%s-%s" % (day, month, year)
                    if len(month) == 3:
                        format == "%d-%b-%Y"
                    else:
                        format == "%d-%B-%Y"
                    date = datetime.strptime(format, testDate)
                    return date
            except ValueError:
                return date


    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("length", 10)
        format = self.get("format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

# =============================================================================
class S3QuestionTypeTimeWidget(S3QuestionTypeAbstractWidget):
    """
        Time Question Type widget

        provides a widget for the survey module that will manage simple
        time questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Time")

# =============================================================================
class S3QuestionTypeOptionWidget(S3QuestionTypeAbstractWidget):
    """
        Option Question Type widget

        provides a widget for the survey module that will manage simple
        option questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of options
        #:            A number one for each option

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.selectionInstructions = "Type x to mark box. Select just one option"
        self.metalist.append("Length")
        self.webwidget = RadioWidget
        self.typeDescription = T("Option")
        self.labelLeft = False
        self.singleRow = False
        self.xlsWidgetSize = [10,0]

    # -------------------------------------------------------------------------
    def display(self, **attr):
        S3QuestionTypeAbstractWidget.initDisplay(self, **attr)
        self.field.requires = IS_IN_SET(self.getList())
        value = self.getAnswer()
        self.field.name = self.question.code
        input = RadioWidget.widget(self.field, value, **self.attr)
        self.field.name = "value"
        return self.layout(self.question.name, input, **attr)

    # -------------------------------------------------------------------------
    def getList(self):
        list = []
        length = self.get("Length")
        if length == None:
            raise Exception("Need to have the options specified")
        for i in range(int(length)):
            list.append(self.get(str(i + 1)))
        return list

    # -------------------------------------------------------------------------
    def getWidgetSize(self, maxWidth = 20):
        """
            function to return the size of the input control
        """
        # calculate the size required for the instructions
        instHeight = 1 + len(self.selectionInstructions)/maxWidth
        if self.singleRow:
            widgetHeight = 1
        else:
            widgetHeight = len(self.getList())
        return (maxWidth/2, instHeight + widgetHeight)

    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict=dict(),
                      answerMatrix=None
                     ):
        """
            Function to write out basic details to the matrix object
        """
        self._store_metadata()
        startrow = row
        startcol = col
        mergeLH = 0
        mergeLV = 0
        maxWidth = 20
        endrow = row
        endcol = col
        lwidth = 10
        lheight = 1
        iwidth = 0
        iheight = 0
        if self.label:
            _TQstn = self._Tquestion(langDict)
            cell = MatrixElement(row,
                                 col,
                                 _TQstn,
                                 style="styleSubHeader"
                                )
            (lwidth, lheight) = self.getLabelSize()
            mergeLH = lwidth - 1
            mergeLV = lheight - 1
            cell.merge(mergeLH,mergeLV)
            matrix.addElement(cell)
            if self.labelLeft:
                col += lwidth
            else:
                row += lheight
            endrow = startrow + lheight
            endcol = startcol + lwidth
            if self.selectionInstructions != None:
                cell = MatrixElement(row,
                                     col,
                                     survey_T(self.selectionInstructions,
                                              langDict),
                                     style="styleInstructions")
                iheight = len(self.selectionInstructions) / maxWidth + 1
                mergeIV = iheight -1
                cell.merge(mergeLH,mergeIV)
                matrix.addElement(cell)
                row += iheight
        list = self.getList()
        if answerMatrix != None:
            answerRow = answerMatrix.lastRow+1
            cell = MatrixElement(answerRow, 0, self.question["code"],
                                 style="styleSubHeader")
            answerMatrix.addElement(cell)
            cell = MatrixElement(answerRow,
                                 1,
                                 len(list),
                                 style="styleSubHeader")
            answerMatrix.addElement(cell)
            cell = MatrixElement(answerRow, 2, "|#|".join(list),
                                 style="styleSubHeader")
            answerMatrix.addElement(cell)
            answerCol = 3
        wwidth = lwidth
        mergeWH = lwidth - 1
        wheight = len(list)
        if self.singleRow:
            wwidthpart = (wwidth - len(list)) / len(list)
            mergeWH = wwidthpart -1
            wheight = 1
        for option in list:
            _TQstn = survey_T(option, langDict)
            cell = MatrixElement(row,
                                 col,
                                 _TQstn,
                                 style="styleText")
            oheight = len(_TQstn)/maxWidth +1
            cell.merge(mergeWH-1,oheight-1)
            matrix.addElement(cell)
            cell = MatrixElement(row, col+mergeWH,"", style="styleInput")
            matrix.addElement(cell)
            if answerMatrix != None:
                cell = MatrixElement(answerRow, answerCol,
                                     self.rowcol_to_cell(row, col + mergeWH),
                                     style="styleText")
                answerMatrix.addElement(cell)
                answerCol += 1
            if self.singleRow:
                col += 1 + wwidthpart
            else:
                row += oheight
        if self.singleRow:
            if endrow < row + 1:
                endrow = row + 1
            if endcol < col:
                endcol = col
        else:
            if endrow < row:
                endrow = row
            if endcol < col + 1 + mergeWH:
                endcol = col + 1 + mergeWH
        self.addPaddingAroundWidget(matrix, startrow, startcol, lwidth, lheight, wwidth, iheight+wheight)
        self.addPaddingToCell(matrix, startrow, startcol, endrow, endcol)
        endrow += self.xlsMargin[1]
        endcol += self.xlsMargin[0]
        if DEBUG:
            # Only for debugging purposes
            self.verifyCoords(endrow, endcol)
        return (endrow, endcol)

    # -------------------------------------------------------------------------
    def writeToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.
        """
        from PyRTF import Paragraph, \
                          Cell, \
                          B
        line = []
        p = Paragraph(ss.ParagraphStyles.Normal)
        p.append(B(str(self.fullName())))
        line.append(Cell(p))
        list = self.getList()
        paras = []
        for option in list:
            p = Paragraph(ss.ParagraphStyles.Normal)
            p.append(survey_T(option, langDict))
            paras.append(p)
        line.append(Cell(*paras))
        return line


    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        if len(valueList) == 0:
            return self.ANSWER_MISSING
        data = valueList[0]
        if data == None:
            return self.ANSWER_MISSING
        self._store_metadata(qstn_id)
        if data in self.getList():
            return self.ANSWER_VALID
        else:
            return self.ANSWER_VALID
        return self.ANSWER_INVALID

# =============================================================================
class S3QuestionTypeOptionYNWidget(S3QuestionTypeOptionWidget):
    """
        YN Question Type widget

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.selectionInstructions = "Type x to mark box."
        self.typeDescription = T("Yes, No")
        self.qstn_metadata["Length"] = 2
        self.singleRow = True

    # -------------------------------------------------------------------------
    def getList(self):
        return ["Yes", "No"]

# =============================================================================
class S3QuestionTypeOptionYNDWidget(S3QuestionTypeOptionWidget):
    """
        Yes, No, Don't Know: Question Type widget

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.selectionInstructions = "Type x to mark box."
        self.typeDescription = T("Yes, No, Don't Know")
        self.qstn_metadata["Length"] = 3

    # -------------------------------------------------------------------------
    def getList(self):
        #T = current.T
        #return [T("Yes"), T("No"), T("Don't Know")]
        return ["Yes", "No", "Don't Know"]

# =============================================================================
class S3QuestionTypeOptionOtherWidget(S3QuestionTypeOptionWidget):
    """
        Option Question Type widget with a final other option attached

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of options
        #:            A number one for each option
        Other:        The question type the other option should be

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.typeDescription = T("Option Other")

    # -------------------------------------------------------------------------
    def getList(self):
        list = S3QuestionTypeOptionWidget.getList(self)
        list.append("Other")
        return list


# =============================================================================
class S3QuestionTypeMultiOptionWidget(S3QuestionTypeOptionWidget):
    """
        Multi Option Question Type widget

        provides a widget for the survey module that will manage options
        questions, where more than one answer can be provided.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.selectionInstructions = "Type x to mark box. Select all applicable options"
        self.typeDescription = current.T("Multi-Option")

    # -------------------------------------------------------------------------
    def display(self, **attr):
        S3QuestionTypeAbstractWidget.initDisplay(self, **attr)
        self.field.requires = IS_IN_SET(self.getList())
        value = self.getAnswer()
        s3 = current.response.s3
        valueList = s3.survey_json2list(value)
        self.field.name = self.question.code
        input = CheckboxesWidget.widget(self.field, valueList, **self.attr)
        self.field.name = "value"
        return self.layout(self.question.name, input, **attr)

# =============================================================================
class S3QuestionTypeLocationWidget(S3QuestionTypeAbstractWidget):
    """
        ***************************************
        **** MULTIPLE CHANGES HAVE OCCURRED ***
        **** REALLY NEEDS TO BE REWRITTEN  ****
        ***************************************
        Location widget: Question Type widget

        provides a widget for the survey module that will link to the
        gis_location table, and provide the record if a match exists.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Parent:    Indicates which question is used to indicate the parent
                   This is used as a simplified Hierarchy.


        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Location")
        self.xlsWidgetSize = [12,0]

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return True
        
    # -------------------------------------------------------------------------
    def display(self, **attr):
        """
            This displays the widget on a web form. It uses the layout
            function to control how the widget is displayed
        """
        return S3QuestionTypeAbstractWidget.display(self, **attr)

    # -------------------------------------------------------------------------
    def getLocationRecord(self, complete_id, location):
        """
            Return the location record from the database
        """
        record = Storage()
        if location != None:
            gtable = current.s3db.gis_location
            query = (gtable.name == location)
            record = current.db(query).select(gtable.name,
                                              gtable.lat,
                                              gtable.lon,
                                             )
            record.complete_id = complete_id
            record.key = location
            if len(record.records) == 0:
                msg = "Unknown Location %s, %s, %s" %(location, query, record.key)
                _debug(msg)
            return record
        else:
            return None

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """
        return value

    # -------------------------------------------------------------------------
    def getAnswerListFromJSON(self, answer):
        """
            If the answer is stored as a JSON value return the data as a map

            If it is not valid JSON then an exception will be raised,
            and must be handled by the calling function
        """
        s3 = current.response.s3
        answerList = s3.survey_json2py(answer)
        return answerList

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("length", 10)
        format = self.get("format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

# =============================================================================
class S3QuestionTypeLinkWidget(S3QuestionTypeAbstractWidget):
    """
        Link widget: Question Type widget

        provides a widget for the survey module that has a link with another
        question.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Parent: The question it links to
        Type: The type of question it really is (another question type)
        Relation: How it relates to the parent question
                  groupby: answers should be grouped by the value of the parent

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.metalist.append("Parent")
        self.metalist.append("Type")
        self.metalist.append("Relation")
        try:
            self._store_metadata()
            type = self.get("Type")
            parent = self.get("Parent")
            if type == None or parent == None:
                self.typeDescription = T("Link")
            else:
                self.typeDescription = T("%s linked to %s") % (type, parent)
        except:
            self.typeDescription = T("Link")

    # -------------------------------------------------------------------------
    def realWidget(self):
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        realWidget.question = self.question
        realWidget.qstn_metadata = self.qstn_metadata
        return realWidget

    # -------------------------------------------------------------------------
    def display(self, **attr):
        return self.realWidget().display(**attr)

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """
        type = self.get("Type")
        return self.realWidget().onaccept(value)

    # -------------------------------------------------------------------------
    def getParentType(self):
        self._store_metadata()
        return self.get("Type")

    # -------------------------------------------------------------------------
    def getParentQstnID(self):
        parent = self.get("Parent")
        query = (self.qtable.code == parent)
        row = current.db(query).select(limitby=(0, 1)).first()
        return row.id

    # -------------------------------------------------------------------------
    def fullName(self):
        return self.question.name

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid 
        """
        return self.realWidget().db_type()

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        return realWidget.validate(valueList, qstn_id)

# =============================================================================
class S3QuestionTypeGridWidget(S3QuestionTypeAbstractWidget):
    """
        Grid widget: Question Type widget

        provides a widget for the survey module that hold a grid of related
        questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Subtitle: The text for the 1st column and 1st row of the grid
        QuestionNo: The number of the first question, used for the question code
        col-cnt:  The number of data columns in the grid
        row-cnt:  The number of data rows in the grid
        columns:  An array of headings for each data column
        rows:     An array of headings for each data row
        data:     A matrix of widgets for each data cell

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.metalist.append("Subtitle")
        self.metalist.append("QuestionNo")
        self.metalist.append("col-cnt")
        self.metalist.append("row-cnt")
        self.metalist.append("columns")
        self.metalist.append("rows")
        self.metalist.append("data")
        self.typeDescription = current.T("Grid")

    # -------------------------------------------------------------------------
    def getMetaData(self, qstn_id=None):
        self._store_metadata(qstn_id=qstn_id, update=True)
        self.subtitle = self.get("Subtitle")
        self.qstnNo = int(self.get("QuestionNo", 1))
        self.colCnt = self.get("col-cnt")
        self.rowCnt = self.get("row-cnt")
        self.columns = json.loads(self.get("columns"))
        self.rows = json.loads(self.get("rows"))
        self.data = json.loads(self.get("data"))

    # -------------------------------------------------------------------------
    def getHeading(self, number):
        self.getMetaData()
        col = (number - self.qstnNo) % int(self.colCnt)
        return self.columns[col]

    # -------------------------------------------------------------------------
    def display(self, **attr):
        S3QuestionTypeAbstractWidget.display(self, **attr)
        complete_id = None
        if "complete_id" in self.question:
            complete_id = self.question.complete_id
        self.getMetaData()
        table = TABLE()
        if self.data != None:
            tr = TR(_class="survey_question")
            if self.subtitle == None:
                tr.append("")
            else:
                tr.append(TH(self.subtitle))
            for col in self.columns:
                if col == None:
                    tr.append("")
                else:
                    tr.append(TH(col))
            table.append(tr)
            posn = 0
            codeNum = self.qstnNo
            for row in self.data:
                tr = TR(_class="survey_question")
                tr.append(TH(self.rows[posn]))
                for cell in row:
                    if cell == "Blank":
                        tr.append("")
                    else:
                        code = "%s%s" % (self.question["code"], codeNum)
                        codeNum += 1
                        childWidget = self.getChildWidget(code)
                        if complete_id != None:
                            childWidget.loadAnswer(complete_id,
                                                   childWidget.id)
                        tr.append(childWidget.subDisplay())
                table.append(tr)
                posn += 1
        return TABLE(table, _border=3)

    # -------------------------------------------------------------------------
    def getMatrixSize(self, maxWidth = 20):
        self._store_metadata()
        self.getMetaData()
        width = 0
        height = 0
        # Add space for the sub heading
        height = 1
        codeNum = self.qstnNo
        labelWidth = maxWidth/2
        for line in range(int(self.rowCnt)):
            label = survey_T(self.rows[line],self.langDict)
            (lwidth, lheight) = (labelWidth, len(label)/(4 * labelWidth / 3) + 1)
            for cell in range(int(self.colCnt)):
                code = "%s%s" % (self.question["code"], codeNum)
                codeNum += 1
                childWidget = self.getChildWidget(code)
                type = childWidget.get("Type")
                realWidget = survey_question_type[type](childWidget.id)
                (cwidth, cheight) = realWidget.getWidgetSize(maxWidth)
                lwidth += cwidth
                if cheight > lheight:
                    lheight = cheight
            height += lheight
            if lwidth > width:
                width = lwidth
        if DEBUG:
            print >> sys.stdout, "%s (%s,%s)" % (self.question["code"], height, width)
        self.xlsWidgetSize = (width,height)
        return (height, width)
        
    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict=dict(),
                      answerMatrix=None,
                      ):
        """
            Function to write out basic details to the matrix object
        """
        self._store_metadata()
        self.getMetaData()
        startrow = row
        startcol = col
        endrow = row
        endcol = col
        maxWidth = 20
        labelWidth = maxWidth / 2
        codeNum = self.qstnNo
        row += 1
        needHeading = True
        # Merge the top left cells
        subtitle = survey_T(self.subtitle,self.langDict)
        cell = MatrixElement(startrow,
                             startcol,
                             subtitle,
                             style="styleSubHeader"
                            )
        cell.merge(labelWidth - 1,0)
        matrix.addElement(cell)
        for line in range(int(self.rowCnt)):
            # Add the label
            label = survey_T(self.rows[line],self.langDict)
            (lwidth, lheight) = (labelWidth, len(label)/(4 * labelWidth / 3) + 1)
            cell = MatrixElement(row,
                                 col,
                                 label,
                                 style="styleSubHeader"
                                )
            cell.merge(lwidth - 1,lheight - 1)
            matrix.addElement(cell)
            maxrow = row + lheight
            endcol = col + lwidth
            for cell in range(int(self.colCnt)):
                code = "%s%s" % (self.question["code"], codeNum)
                codeNum += 1
                childWidget = self.getChildWidget(code)
                type = childWidget.get("Type")
                realWidget = survey_question_type[type](childWidget.id)
                realWidget.label = False
                #realWidget.xlsMargin = (0,0)
                col = endcol
                realWidget.startPosn = (col, row)
                (endrow, endcol) = realWidget.writeToMatrix(matrix,
                                                             row,
                                                             col,
                                                             langDict,
                                                             answerMatrix
                                                            )
                if endrow > maxrow:
                    maxrow = endrow
                if needHeading:
                    # Now add the heading for this column
                    label = survey_T(self.columns[cell],self.langDict)
                    cell = MatrixElement(startrow,
                                         col,
                                         label,
                                         style="styleSubHeader"
                                        )
                    cell.merge(endcol - col -1 ,0)
                    matrix.addElement(cell)
            row = maxrow
            col = startcol
            needHeading = False
        # Add widget padding
        self.addPaddingToCell(matrix, startrow, startcol, row, endcol)
        row += self.xlsMargin[1]
        endcol += self.xlsMargin[0]
        return (row, endcol)

    # -------------------------------------------------------------------------
    def writeToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            This will just display the grid name, following this will be the
            grid child objects.
        """
        from PyRTF import Paragraph, \
                          Cell, \
                          B
        line = []
        p = Paragraph(ss.ParagraphStyles.NormalCentre)
        p.append(B(self.question.name))
        line.append(Cell(p, span=2))
        return line

    # -------------------------------------------------------------------------
    def insertChildren(self, record, metadata):
        self.id = record.id
        self.question = record
        self.qstn_metadata = metadata
        self.getMetaData()
        if self.data != None:
            posn = 0
            qstnNo = self.qstnNo
            parent_id = self.id
            parent_code = self.question["code"]
            for row in self.data:
                name = self.rows[posn]
                posn += 1
                for cell in row:
                    if cell == "Blank":
                        continue
                    else:
                        type = cell
                        code = "%s%s" % (parent_code, qstnNo)
                        qstnNo += 1
                        childMetadata = self.get(code)
                        if childMetadata == None:
                            childMetadata = {}
                        else:
                            childMetadata = json.loads(childMetadata)
                        childMetadata["Type"] = type
                        # web2py stomps all over a list so convert back to a string
                        # before inserting it on the database
                        metadata = json.dumps(childMetadata)
                        try:
                            id = self.qtable.insert(name = name,
                                                    code = code,
                                                    type = "GridChild",
                                                    metadata = metadata,
                                                   )
                        except:
                            record = self.qtable(code = code)
                            id = record.id
                            record.update_record(name = name,
                                                 code = code,
                                                 type = "GridChild",
                                                 metadata = metadata,
                                                )
                        record = self.qtable(id)
                        current.manager.s3.survey_updateMetaData(record,
                                                                 "GridChild",
                                                                 childMetadata)

    # -------------------------------------------------------------------------
    def insertChildrenToList(self, question_id, template_id, section_id,
                             qstn_posn):
        self.getMetaData(question_id)
        if self.data != None:
            posn = 0
            qstnNo = self.qstnNo
            qstnPosn = 1
            parent_id = self.id
            parent_code = self.question["code"]
            for row in self.data:
                name = self.rows[posn]
                posn += 1
                for cell in row:
                    if cell == "Blank":
                        continue
                    else:
                        code = "%s%s" % (parent_code, qstnNo)
                        qstnNo += 1
                        record = self.qtable(code = code)
                        id = record.id
                        try:
                            self.qltable.insert(question_id = id,
                                                template_id = template_id,
                                                section_id = section_id,
                                                posn = qstn_posn+qstnPosn,
                                               )
                            qstnPosn += 1
                        except:
                            pass # already on the database no change required

    # -------------------------------------------------------------------------
    def getChildWidget (self, code):
            # Get the question from the database
            query = (self.qtable.code == code)
            question = current.db(query).select(limitby=(0, 1)).first()
            if question == None:
                raise Exception("no question with code %s in database" % code)
            cellWidget = survey_question_type["GridChild"](question.id)
            return cellWidget

# =============================================================================
class S3QuestionTypeGridChildWidget(S3QuestionTypeAbstractWidget):
    """
        GridChild widget: Question Type widget

        provides a widget for the survey module that is held by a grid question
        type an provides a link to the true question type.

        Available metadata for this class:
        Type:     The type of question it really is (another question type)

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        if self.question != None and "code" in self.question:
            # Expect the parent code to be the same as the child with the number
            # removed. This means that the parent code must end with a hyphen.
            end = self.question.code.rfind("-")+1
            parentCode = self.question.code[0:end]
            parentNumber = self.question.code[end:]
            self.question.parentCode = parentCode
            self.question.parentNumber = int(parentNumber)
        self.metalist.append("Type")
        self.typeDescription = self.qstn_metadata["Type"]
        self.xlsWidgetSize = (0, 0)

    # -------------------------------------------------------------------------
    def display(self, **attr):
        return None

    # -------------------------------------------------------------------------
    def realWidget(self):
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        realWidget.question = self.question
        realWidget.qstn_metadata = self.qstn_metadata
        return realWidget

    # -------------------------------------------------------------------------
    def subDisplay(self, **attr):
        S3QuestionTypeAbstractWidget.display(self, **attr)
        return self.realWidget().display(question_id=self.id, display = "Control Only")

    # -------------------------------------------------------------------------
    def getParentType(self):
        self._store_metadata()
        return self.get("Type")

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid 
        """
        return self.realWidget().db_type()

    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict=dict(),
                      answerMatrix=None,
                      style={}
                     ):
        """
            Dummy function that doesn't write anything to the matrix,
            because it is handled by the Grid question type
        """
        return (row, col)

    # -------------------------------------------------------------------------
    def writeToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.
        """
        return self.realWidget().writeToRTF(ss,langDict)


###############################################################################
###  Classes for analysis
###    will work with a list of answers for the same question
###############################################################################

# Analysis Types
def analysis_stringType(question_id, answerList):
    return S3StringAnalysis("String", question_id, answerList)
def analysis_textType(question_id, answerList):
    return S3TextAnalysis("Text", question_id, answerList)
def analysis_numericType(question_id, answerList):
    return S3NumericAnalysis("Numeric", question_id, answerList)
def analysis_dateType(question_id, answerList):
    return S3DateAnalysis("Date", question_id, answerList)
def analysis_timeType(question_id, answerList):
    return S3TimeAnalysis("Date", question_id, answerList)
def analysis_optionType(question_id, answerList):
    return S3OptionAnalysis("Option", question_id, answerList)
def analysis_ynType(question_id, answerList):
    return S3OptionYNAnalysis("YesNo", question_id, answerList)
def analysis_yndType(question_id, answerList):
    return S3OptionYNDAnalysis("YesNoDontKnow", question_id, answerList)
def analysis_optionOtherType(question_id, answerList):
    return S3OptionOtherAnalysis("OptionOther", question_id, answerList)
def analysis_multiOptionType(question_id, answerList):
    return S3MultiOptionAnalysis("MultiOption", question_id, answerList)
def analysis_locationType(question_id, answerList):
    return S3LocationAnalysis("Location", question_id, answerList)
def analysis_linkType(question_id, answerList):
    return S3LinkAnalysis("Link", question_id, answerList)
def analysis_gridType(question_id, answerList):
    return S3GridAnalysis("Grid", question_id, answerList)
def analysis_gridChildType(question_id, answerList):
    return S3GridChildAnalysis("GridChild", question_id, answerList)
#def analysis_ratingType(answerList):
#    return S3RatingAnalysis(answerList)
#    pass

survey_analysis_type = {
    "String": analysis_stringType,
    "Text": analysis_textType,
    "Numeric": analysis_numericType,
    "Date": analysis_dateType,
    "Time": analysis_timeType,
    "Option": analysis_optionType,
    "YesNo": analysis_ynType,
    "YesNoDontKnow": analysis_yndType,
    "OptionOther": analysis_optionOtherType,
    "MultiOption" : analysis_multiOptionType,
    "Location": analysis_locationType,
    "Link": analysis_linkType,
    "Grid": analysis_gridType,
    "GridChild" : analysis_gridChildType,
    #"Rating": analysis_ratingType,
}

# =============================================================================
class S3AnalysisPriority():
    def __init__(self,
                 range=[-1, -0.5, 0, 0.5, 1],
                 colour={-1:"#888888", # grey
                          0:"#000080", # blue
                          1:"#008000", # green
                          2:"#FFFF00", # yellow
                          3:"#FFA500", # orange
                          4:"#FF0000", # red
                          5:"#880088", # purple
                        },
                 # Make Higher-priority show up more clearly
                 opacity={-1:0.5,
                           0:0.6,
                           1:0.6,
                           2:0.7,
                           3:0.7,
                           4:0.8,
                           5:0.8,
                        },
                 image={-1:"grey",
                         0:"blue",
                         1:"green",
                         2:"yellow",
                         3:"orange",
                         4:"red",
                         5:"purple",
                        },
                 desc={-1:"No Data",
                        0:"Very Low",
                        1:"Low",
                        2:"Medium Low",
                        3:"Medium High",
                        4:"High",
                        5:"Very High",
                        },
                 zero = True
                 ):
        self.range = range
        self.colour = colour
        self.opacity = opacity
        self.image = image
        self.description = desc

    # -------------------------------------------------------------------------
    def imageURL(self, app, key):
        T = current.T
        base_url = "/%s/static/img/survey/" % app
        dot_url = base_url + "%s-dot.png" % self.image[key]
        image = IMG(_src=dot_url,
                    _alt=T(self.image[key]),
                    _height=12,
                    _width=12,
                   )
        return image

    # -------------------------------------------------------------------------
    def desc(self, key):
        T = current.T
        return T(self.description[key])

    # -------------------------------------------------------------------------
    def rangeText(self, key, pBand):
        T = current.T
        if key == -1:
            return ""
        elif key == 0:
            return T("At or below %s" % (pBand[1]))
        elif key == len(pBand)-1:
            return T("Above %s" % (pBand[len(pBand)-1]))
        else:
            return "%s - %s" % (pBand[key], pBand[key+1])

# -----------------------------------------------------------------------------
class S3AbstractAnalysis():
    """
        Abstract class used to hold all the responses for a single question
        and perform some simple analysis on the data.

        This class holds the main functions for:
         * displaying tables of results
         * displaying charts
         * grouping the data.

        Properties
        ==========
        question_id    - The id from the database
        answerList     - A list of answers, taken from the survey_answer
                         id, complete_id and value
                         See models/survey.py getAllAnswersForQuestionInSeries()
        valueList      - A list of validated & sanitised values
        result         - A list of results before formatting
        type           - The question type
        qstnWidget     - The question Widget for this question
        priorityGroup  - The type of priority group to use in the map
        priorityGroups - The priority data used to colour the markers on the map
    """

    def __init__(self,
                 type,
                 question_id,
                 answerList,
                ):
        self.question_id = question_id
        self.answerList = answerList
        self.valueList = []
        self.result = []
        self.type = type
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.priorityGroup = "zero" # Ensures that it doesn't go negative
        self.priorityGroups = {"default" : [-1, -0.5, 0, 0.5, 1],
                               "standard" : [-2, -1, 0, 1, 2],
                               }
        for answer in self.answerList:
            if self.valid(answer):
                try:
                    cast = self.castRawAnswer(answer["complete_id"],
                                              answer["value"])
                    if cast != None:
                        self.valueList.append(cast)
                except:
                    if DEBUG:
                        raise
                    pass

        self.basicResults()

    # -------------------------------------------------------------------------
    def valid(self, answer):
        """
            used to validate a single answer
        """
        # @todo add validation here
        # widget = S3QuestionTypeNumericWidget()
        # widget.validate(answer)
        # if widget.ANSWER_VALID:
        return True

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        """
            Used to modify the answer from its raw text format.
            Where necessary, this will function be overridden.
        """
        return answer

    # -------------------------------------------------------------------------
    def basicResults(self):
        """
            Perform basic analysis of the answer set.
            Where necessary, this will function be overridden.
        """
        pass

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        """
            This will display a button which when pressed will display a chart
            When a chart is not appropriate then the subclass will override this
            function with a nul function.
        """
        if len(self.valueList) == 0:
            return None
        if series_id == None:
            return None
        src = URL(r=current.request,
                  f="completed_chart",
                  vars={"question_id":self.question_id,
                        "series_id" : series_id,
                        "type" : self.type
                        }
                 )
        link = A(current.T("Chart"), _href=src, _target="blank",
                 _class="action-btn")
        return DIV(link, _class="surveyChart%sWidget" % self.type)

    # -------------------------------------------------------------------------
    def getChartName(self, series_id):
        import hashlib
        request = current.request
        h = hashlib.sha256()
        h.update(self.qstnWidget.question.code)
        encoded_part = h.hexdigest()
        chartName = "survey_series_%s_%s" % \
                    (series_id,
                     encoded_part
                    )
        return chartName

    # -------------------------------------------------------------------------
    def drawChart(self, series_id, output=None, data=None, label=None,
                  xLabel=None, yLabel=None):
        """
            This function will draw the chart using the answer set.

            This function must be overridden by the subclass.
        """
        msg = "Programming Error: No chart for %sWidget" % self.type
        output = StringIO()
        output.write(msg)
        current.response.body = output

    # -------------------------------------------------------------------------
    def summary(self):
        """
            Calculate a summary of basic data.

            Where necessary, this will function be overridden.
        """
        self.result = []
        return self.count()

    # -------------------------------------------------------------------------
    def count(self):
        """
            Create a basic count of the data set.

            Where necessary, this will function be overridden.
        """
        self.result.append(([current.T("Replies")], len(self.answerList)))
        return self.format()

    # -------------------------------------------------------------------------
    def format(self):
        """
            This function will take the results and present them in a HTML table
        """
        table = TABLE()
        for (key, value) in self.result:
            table.append(TR(TD(B(key)), TD(value)))
        return table

    # -------------------------------------------------------------------------
    def uniqueCount(self):
        """
            Calculate the number of occurances of each value
        """
        map = {}
        for answer in self.valueList:
            if answer in map:
                map[answer] += 1
            else:
                map[answer] = 1
        return map

    # -------------------------------------------------------------------------
    def groupData(self, groupAnswer):
        """
            method to group the answers by the categories passed in
            The categories will belong to another question.

            For example the categories might be an option question which has
            responses from High, Medium and Low. So all the responses that
            correspond to the High category will go into one group, the Medium
            into a second group and Low into the final group.

            Later these may go through a filter which could calculate the
            sum, or maybe the mean. Finally the result will be split.

            See controllers/survey.py - series_graph()
        """
        grouped = {}
        answers = {}
        for answer in self.answerList:
            # hold the raw value (filter() will pass the value through castRawAnswer()
            answers[answer["complete_id"]] = answer["value"]
        # Step through each of the responses on the categories question
        for ganswer in groupAnswer:
            gcode = ganswer["complete_id"]
            greply = ganswer["value"]
            # If response to the group question also has a response to the main question
            # Then store the response in value, otherwise return an empty list for this response
            if gcode in answers:
                value = answers[gcode]
                if greply in grouped:
                    grouped[greply].append(value)
                else:
                    grouped[greply] = [value]
            else:
                if greply not in grouped:
                    grouped[greply] = []
        return grouped

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        """
            Filter the data within the groups by the filter type
        """
        return groupedData

    # -------------------------------------------------------------------------
    def splitGroupedData(self, groupedData):
        """
            Split the data set by the groups
        """
        keys = []
        values = []
        for (key, value) in groupedData.items():
            keys.append(key)
            values.append(value)
        return (keys, values)

# =============================================================================
class S3StringAnalysis(S3AbstractAnalysis):

    def chartButton(self, series_id):
        return None

# =============================================================================
class S3TextAnalysis(S3AbstractAnalysis):

    def chartButton(self, series_id):
        return None

# =============================================================================
class S3DateAnalysis(S3AbstractAnalysis):

    def chartButton(self, series_id):
        return None

# -----------------------------------------------------------------------------
class S3TimeAnalysis(S3AbstractAnalysis):

    def chartButton(self, series_id):
        return None

# =============================================================================
class S3NumericAnalysis(S3AbstractAnalysis):

    def __init__(self,
                 type,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, type, question_id, answerList)
        self.histCutoff = 10

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        try:
            return float(answer)
        except:
            return None

    # -------------------------------------------------------------------------
    def summary(self):
        T = current.T
        widget = S3QuestionTypeNumericWidget()
        fmt = widget.formattedAnswer
        if self.sum:
            self.result.append(([T("Total")], fmt(self.sum)))
        if self.average:
            self.result.append(([T("Average")], fmt(self.average)))
        if self.max:
            self.result.append(([T("Maximum")], fmt(self.max)))
        if self.min:
            self.result.append(([T("Minimum")], fmt(self.min)))
        return self.format()

    # -------------------------------------------------------------------------
    def count(self):
        T = current.T
        self.result.append((T("Replies"), len(self.answerList)))
        self.result.append((T("Valid"), self.cnt))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        self.cnt = 0
        if len(self.valueList) == 0:
            self.sum = None
            self.average = None
            self.max = None
            self.min = None
            return
        self.sum = 0
        self.max = self.valueList[0]
        self.min = self.valueList[0]
        for answer in self.valueList:
            self.cnt += 1
            self.sum += answer
            if answer > self.max:
                self.max = answer
            if answer < self.min:
                self.min = answer
        self.average = self.sum / float(self.cnt)

    # -------------------------------------------------------------------------
    def advancedResults(self):
        try:
            from numpy import array
        except:
            print >> sys.stderr, "ERROR: S3Survey requires numpy library installed."

        array = array(self.valueList)
        self.std = array.std()
        self.mean = array.mean()
        self.zscore = {}
        for answer in self.answerList:
            complete_id = answer["complete_id"]
            try:
                value = self.castRawAnswer(complete_id, answer["value"])
            except:
                continue
            if value != None:
                self.zscore[complete_id] = (value - self.mean) / self.std

    # -------------------------------------------------------------------------
    def priority(self, complete_id, priorityObj):
        priorityList = priorityObj.range
        priority = 0
        try:
            zscore = self.zscore[complete_id]
            for limit in priorityList:
                if zscore <= limit:
                    return priority
                priority += 1
            return priority
        except:
            return -1

    # -------------------------------------------------------------------------
    def priorityBand(self, priorityObj):
        priorityList = priorityObj.range
        priority = 0
        band = [""]
        cnt = 0
        for limit in priorityList:
            value = int(self.mean + limit * self.std)
            if value < 0:
                value = 0
                priorityList[cnt] = - self.mean / self.std
            band.append(value)
            cnt += 1
        return band

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        # At the moment only draw charts for integers
        if self.qstnWidget.get("Format", "n") != "n":
            return None
        if len(self.valueList) < self.histCutoff:
            return None
        return S3AbstractAnalysis.chartButton(self, series_id)

    # -------------------------------------------------------------------------
    def drawChart(self, series_id, output="xml",
                  data=None, label=None, xLabel=None, yLabel=None):
        chartFile = self.getChartName(series_id)
        cached = S3Chart.getCachedFile(chartFile)
        if cached:
            return cached

        chart = S3Chart(path=chartFile)
        chart.asInt = True
        if data == None:
            chart.survey_hist(self.qstnWidget.question.name,
                              self.valueList,
                              10,
                              0,
                              self.max,
                              xlabel = self.qstnWidget.question.name,
                              ylabel = current.T("Count")
                             )
        else:
            chart.survey_bar(self.qstnWidget.question.name,
                             data,
                             label,
                             []
                            )
        image = chart.draw(output=output)
        return image

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        filteredData = {}
        if filterType == "Sum":
            for (key, valueList) in groupedData.items():
                sum = 0
                for value in valueList:
                    try:
                        sum += self.castRawAnswer(None, value)
                    except:
                        pass
                filteredData[key] = sum
            return filteredData
        return groupedData


# =============================================================================
class S3OptionAnalysis(S3AbstractAnalysis):

    # -------------------------------------------------------------------------
    def summary(self):
        T = current.T
        for (key, value) in self.listp.items():
            self.result.append((T(key), value))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        self.cnt = 0
        self.list = {}
        for answer in self.valueList:
            self.cnt += 1
            if answer in self.list:
                self.list[answer] += 1
            else:
                self.list[answer] = 1
        self.listp = {}
        if self.cnt != 0:
            for (key, value) in self.list.items():
                self.listp[key] = "%3.1f%%" % round((100.0 * value) / self.cnt,1)

    # -------------------------------------------------------------------------
    def drawChart(self, series_id, output="xml",
                  data=None, label=None, xLabel=None, yLabel=None):
        chartFile = self.getChartName(series_id)
        cached = S3Chart.getCachedFile(chartFile)
        if cached:
            return cached

        chart = S3Chart(path=chartFile)
        data = []
        label = []
        for (key, value) in self.list.items():
            data.append(value)
            label.append(key)
        chart.survey_pie(self.qstnWidget.question.name,
                         data,
                         label)
        image = chart.draw(output=output)
        return image

# =============================================================================
class S3OptionYNAnalysis(S3OptionAnalysis):

    # -------------------------------------------------------------------------
    def summary(self):
        T = current.T
        self.result.append((T("Yes"), self.yesp))
        self.result.append((T("No"), self.nop))
        return self.format()


    # -------------------------------------------------------------------------
    def basicResults(self):
        S3OptionAnalysis.basicResults(self)
        T = current.T
        if "Yes" in self.listp:
            self.yesp = self.listp["Yes"]
        else:
            if self.cnt == 0:
                self.yesp = "" # No replies so can't give a percentage
            else:
                self.list["Yes"] = 0
                self.yesp = T("0%")
        if "No" in self.listp:
            self.nop = self.listp["No"]
        else:
            if self.cnt == 0:
                self.nop =  "" # No replies so can't give a percentage
            else:
                self.list["No"] = 0
                self.nop = T("0%")

# =============================================================================
class S3OptionYNDAnalysis(S3OptionAnalysis):

    # -------------------------------------------------------------------------
    def summary(self):
        T = current.T
        self.result.append((T("Yes"), self.yesp))
        self.result.append((T("No"), self.nop))
        self.result.append((T("Don't Know"), self.dkp))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        S3OptionAnalysis.basicResults(self)
        T = current.T
        if "Yes" in self.listp:
            self.yesp = self.listp["Yes"]
        else:
            if self.cnt == 0:
                self.yesp = "" # No replies so can't give a percentage
            else:
                self.list["Yes"] = 0
                self.yesp = T("0%")
        if "No" in self.listp:
            self.nop = self.listp["No"]
        else:
            if self.cnt == 0:
                self.nop = "" # No replies so can't give a percentage
            else:
                self.list["No"] = 0
                self.nop = T("0%")
        if "Don't Know" in self.listp:
            self.dkp = self.listp["Don't Know"]
        else:
            if self.cnt == 0:
                self.dkp = "" # No replies so can't give a percentage
            else:
                self.list["Don't Know"] = 0
                self.dkp = T("0%")

# =============================================================================
class S3OptionOtherAnalysis(S3OptionAnalysis):
    pass

# =============================================================================
class S3MultiOptionAnalysis(S3OptionAnalysis):

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        """
            Used to modify the answer from its raw text format.
            Where necessary, this function will be overridden.
        """
        valueList = current.s3db.survey_json2list(answer)
        return valueList

    # -------------------------------------------------------------------------
    def basicResults(self):
        self.cnt = 0
        self.list = {}
        for answer in self.valueList:
            if isinstance(answer, list):
                answerList = answer
            else:
                answerList = [answer]
            self.cnt += 1
            for answer in answerList:
                if answer in self.list:
                    self.list[answer] += 1
                else:
                    self.list[answer] = 1
        self.listp = {}
        if self.cnt != 0:
            for (key, value) in self.list.items():
                self.listp[key] = "%s%%" %((100 * value) / self.cnt)

    # -------------------------------------------------------------------------
    def drawChart(self, series_id, output="xml",
                  data=None, label=None, xLabel=None, yLabel=None):
        chartFile = self.getChartName(series_id)
        cached = S3Chart.getCachedFile(chartFile)
        if cached:
            return cached

        chart = S3Chart(path=chartFile)
        data = []
        label = []
        for (key, value) in self.list.items():
            data.append(value)
            label.append(key)
        chart.survey_bar(self.qstnWidget.question.name,
                         data,
                         label,
                         None
                         )
        image = chart.draw(output=output)
        return image

# =============================================================================
class S3LocationAnalysis(S3AbstractAnalysis):
    """
        Widget for analysing Location type questions

        The analysis will compare the location values provided with
        data held on the gis_location table.

        The data held can be in its raw form (the actual value imported) or
        in a more refined state, which may include the actual location id
        held on the database or an alternative value which is a string.

        The raw value may be a local name for the place whilst the altervative
        value should be the actual value held on the database.
        The alternative value is useful for matching duplicate responses that
        are using the same local name.
    """

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        """
            Convert the answer for the complete_id into a database record.

            This can have one of three type of return values.
            A single record: The actual location
            Multiple records: The set of location, on of which is the location
            None: No match is found on the database.
        """
        records = self.qstnWidget.getLocationRecord(complete_id, answer)
        return records

    # -------------------------------------------------------------------------
    def summary(self):
        """
            Returns a summary table
        """
        T = current.T
        self.result.append((T("Known Locations"), self.kcnt))
        self.result.append((T("Duplicate Locations"), self.dcnt))
        self.result.append((T("Unknown Locations"), self.ucnt))
        return self.format()

    # -------------------------------------------------------------------------
    def count(self):
        """
            Returns a table of basic results
        """
        T = current.T
        self.result.append((T("Total Locations"), len(self.valueList)))
        self.result.append((T("Unique Locations"), self.cnt))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        """
            Calculate the basic results, which consists of a number of list
            related to the locations

            LISTS (dictionaries)
            ====================
            All maps are keyed on the value used in the database lookup
            locationList - holding the number of times the value exists
            complete_id  - a list of complete_id at this location
            duplicates   - a list of duplicate records
            known        - The record from the database

            Calculated Values
            =================
            cnt  - The number of unique locations
            dcnt - The number of locations with duplicate values
            kcnt - The number of known locations (single match on the database)
            ucnt - The number of unknown locations
            dper - The percentage of locations with duplicate values
            kper - The percentage of known locations
            NOTE: Percentages are calculated from the unique locations
                  and not from the total responses.
        """
        self.locationList = {}
        self.duplicates = {}
        self.known = {}
        self.complete_id = {}
        for answer in self.valueList:
            if answer != None:
                key = answer.key
                if key in self.locationList:
                    self.locationList[key] += 1
                else:
                    self.locationList[key] = 1
                    if key in self.complete_id:
                        self.complete_id[key].append(answer.complete_id)
                    else:
                        self.complete_id[key] = [answer.complete_id]
                    result = answer.records
                    if len(result) > 1:
                        self.duplicates[key] = result
                    if len(result) == 1:
                        self.known[key] = result[0]
        self.cnt = len(self.locationList)
        self.dcnt = len(self.duplicates)
        self.kcnt = len(self.known)
        if self.cnt == 0:
            self.dper = "0%%"
            self.kper = "0%%"
        else:
            self.dper = "%s%%" %((100 * self.dcnt) / self.cnt)
            self.kper = "%s%%" %((100 * self.kcnt) / self.cnt)
        self.ucnt = self.cnt - self.kcnt - self.dcnt

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        """
            Ensures that no button is set up
        """
        return None

    # -------------------------------------------------------------------------
    def uniqueCount(self):
        """
            Calculate the number of occurances of each value
        """
        map = {}
        for answer in self.valueList:
            if answer.key in map:
                map[answer.key] += 1
            else:
                map[answer.key] = 1
        return map

# =============================================================================
class S3LinkAnalysis(S3AbstractAnalysis):

    def __init__(self,
                 type,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, type, question_id, answerList)
        linkWidget = S3QuestionTypeLinkWidget(question_id)
        parent = linkWidget.get("Parent")
        relation = linkWidget.get("Relation")
        type = linkWidget.get("Type")
        parent_qid = linkWidget.getParentQstnID()
        valueMap = {}
        for answer in self.answerList:
            complete_id = answer["complete_id"]
            parent_answer = linkWidget.loadAnswer(complete_id,
                                                  parent_qid,
                                                  forceDB=True
                                                 )
            if relation == "groupby":
                # @todo: check for different values
                valueMap.update({parent_answer:answer})
        valueList = []
        for answer in valueMap.values():
            valueList.append(answer)
        self.widget = survey_analysis_type[type](question_id, valueList)

    # -------------------------------------------------------------------------
    def summary(self):
        return self.widget.summary()

    # -------------------------------------------------------------------------
    def count(self):
        return self.widget.count()

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        return self.widget.chartButton(series_id)

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        return self.widget.filter(filterType, groupedData)

    # -------------------------------------------------------------------------
    def drawChart(self, series_id, output="xml",
                  data=None, label=None, xLabel=None, yLabel=None):
        return self.widget.drawChart(data, series_id, label, xLabel, yLabel)

# =============================================================================
class S3GridAnalysis(S3AbstractAnalysis):
    pass

# =============================================================================
class S3GridChildAnalysis(S3AbstractAnalysis):

    def __init__(self,
                 type,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, type, question_id, answerList)
        childWidget = S3QuestionTypeLinkWidget(question_id)
        trueType = childWidget.get("Type")
        for answer in self.answerList:
            if self.valid(answer):
                try:
                    self.valueList.append(trueType.castRawAnswer(answer["complete_id"],
                                                                 answer["value"]))
                except:
                    pass
        self.widget = survey_analysis_type[trueType](question_id, self.answerList)

    # -------------------------------------------------------------------------
    def drawChart(self,
                  series_id,
                  output="xml",
                  data=None,
                  label=None,
                  xLabel=None,
                  yLabel=None):
        return self.widget.drawChart(series_id, output, data, label, xLabel, yLabel)

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        return self.widget.filter(filterType, groupedData)

# END =========================================================================
