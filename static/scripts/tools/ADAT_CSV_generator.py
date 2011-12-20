#!/usr/bin/python
"""
    Sahana-Eden ADAT helper script
    ==============================

    Script to generate the import files for a new survey template.
    The input is a "xls" spreadsheet with four sheets, namely:
     * Template
     * Sections
     * Questions
     * Layout

    The output is two csv files one that can beused to import the
    questions into the system, the other that may be used to import
    the layout details into the system. The name of the files will the
    same as the input file with either the .Layout.csv or .Question.csv prefix
    replacing the .xls type.

    Details of the input sheets
    ===========================

    Template
    --------
    This includes the basic details of the template as follows:
    A1: Template Name
    A2: Template Description
    A3: Complete Question
    A4: Date Question
    A5: Time Question
    A6: Location Question
    A7: Priority Question

    The questions in cells A3:A7 are the unique questions codes which are given
    later in sheet the Questions sheet.

    Sections
    --------
    This lists each section within the template. Each section name is given in
    the A column, they should be provided in their default order. Thier display
    order can be later be changed by the layout but this will be the default
    order of the sections.

    Questions
    ---------
    This holds details of questions in each column as follows:
    A: Unique Question Code
    B: The Section    - the section to which the question belongs
    C: Question Name  - the actual question which is what will be displayed
                        and should be in the base template language (English)
    D: Question type  - This must be one of the known question widget types
    E: Question notes - any help information that should be associated with
                        the question to help the enumerators complete
                        the questionnaire.
    F onwards: Metadata
      Any option type:  The list of options, thus:
                        OptionOther: Early   Continue
      The Grid type: This is the most complex type when it comes to the metadata
                     and it relies on keywords to make it as simple as possible.
                     The columns alternate between keywords and their value.
                     The valid keywords are:
                     Subtitle -        the subtitle of the grid [Optional]
                     Column count -    the number of columns in the grid
                     Row count -       the number of rows in the grid
                     Column Headings - the headings for each column with one
                                       heading per cell
                     Row Questions -   the headings for each row with one
                                       heading per cell
                     Question Type -   this is the type of each question, again
                                       this must be one of the known question
                                       widget types. If just one value is given
                                       then all questions take this type. If the
                                       same number of types as columns are given
                                       then this type reflects the types used
                                       in each column. Otherwise, their should
                                       be a direct mapping between question and
                                       type.
                     GridChild -       Some of the question types need to have
                                       metadata associated with them. This 
                                       keyword is followed by a number to
                                       indicate which question type the metadata
                                       is for, refering to the order in the
                                       Question Type list. [Optional]
                     NOTE: The metadata must be provided in this order.

    NOTE on the grid question type:
         The question code for this should be unique and end with a hyphen.
         The questions within the grid will then be properly numbered.
         So a grid question code of PMI-WASH-A-, will then hold the questions
         PMI-WASH-A-1, PMI-WASH-A-2, PMI-WASH-A-3 etc.


    Layout
    ------
    This is used to describe in a semi-visual way how the questions should be
    laid out. This layout can be used for any representation of the
    questionnaire such as web form, spreadsheet, PDF etc.

    The rules to complete this section are as follows:
     * Add the section name
     * On subsequent lines add the question codes for the questions to appear
       in this section
     * For questions that are to appear in a the same line add them in adjacent
       columns of the same row, thus:
       PMI-Ass-1    PMI-Ass-2    PMI-Ass-3
     * For questions that are to appear in adjacent columns use the keyword
       column in the first column and then add the questions in subsequent
       columns, thus:
       columns  PMI-Health-1    PMI-Health-4    PMI-Health-A-
                PMI-Health-2
       So this describes three columns with two questions in the first column
       and one question each in columns 2 and 3.
     * To add a subheading (normally at the start of a column) just add the
       text in the cell and the question codes in the columns below. Any text
       that does not match a question code or keyword is assumed to be a
       subheading.

     NOTE: The script might be able to manage blank lines between the end of
           one section and the next but *please* try and avoid using blank lines
           since this is not fully tested and future enhancements of this script
           may break that.
     NOTE: Only include questions codes from within the section. Including
           questions from different sections is untested and whilst the script
           may work as expected, Sahana-Eden *might* not.

"""
import sys
import xlrd
import csv

optionTypes = ["Option", "OptionOther", "MultiOption"]
widgetTypes = ["String", "Text", "Numeric", "Date", "Option", "YesNo", "YesNoDontKnow", "OptionOther", "MultiOption", "Location", "Link", "Grid", "GridChild"]
layoutQuestions = []

def splitGridChildMetadata(metadataList):
    gridChildList = []
    dataList = []
    for x in range(len(metadataList)):
        if metadataList[x] == "GridChild":
            if dataList != []:
                gridChildList.append(dataList)
            dataList = []
        else:
            dataList.append(metadataList[x])
    if dataList != []:
        gridChildList.append(dataList)
    return gridChildList

def processGridChildMetadata(metadataList, childType):
    metadata = dict()
    gridChildList  = splitGridChildMetadata(metadataList)
    for x in range(len(gridChildList)):
        dataList = gridChildList[x]
        qstnNo = int(dataList[0])
        qstn_type = childType[qstnNo-1]
        (metadataList, dummy) = processMetadata(dataList[1:], qstn_type, None,0,None)
        metadata[qstnNo] = metadataList
    return metadata

def processGridChildMetadataAll(metadataList, colCnt, rowCnt, qstn_code, qstn_posn, firstQstnInSection, childType):
    metadata = dict()
    qstnMetadataList = processGridChildMetadata(metadataList, childType)
    offset = qstn_posn - firstQstnInSection + 1
    for x in range(colCnt * rowCnt):
        qCode = "%s%d" %(qstn_code, x+offset)
        for qstnMetadata in qstnMetadataList.values():
            metadata[str(qCode)] = qstnMetadata
    return metadata

def processGridChildMetadataColumn(metadataList, colCnt, rowCnt, qstn_code, qstn_posn, firstQstnInSection, childType):
    metadata = dict()
    qstnMetadataList = processGridChildMetadata(metadataList, childType)
    offset = qstn_posn - firstQstnInSection
    for (posn, qstnMetadata) in qstnMetadataList.items():
        for x in range(rowCnt):
            qCode = "%s%d" %(qstn_code, x*colCnt+posn+offset)
            metadata[str(qCode)] = qstnMetadata
    return metadata

def processGridChildMetadataElement(metadataList, qstn_code, qstn_posn, firstQstnInSection, childType):
    metadata = dict()
    qstnMetadataList = processGridChildMetadata(metadataList, childType)
    offset = qstn_posn - firstQstnInSection
    for (posn, qstnMetadata) in qstnMetadataList.items():
        qCode = "%s%d" %(qstn_code, posn+offset)
        metadata[str(qCode)] = qstnMetadata
    return metadata

def processMetadata(metadataList, qstn_type, qstn_code, qstn_posn, firstQstnInSection):
    metadata = dict()
    next_qstn_posn = qstn_posn + 1
    if qstn_type in optionTypes:
        posn = 0
        for value in metadataList:
            posn += 1
            if value == "metadata":
                metadata += processMetadata(metadataList[posn:],None,None,0,None)
                break
            metadata[posn] = str(value)
        metadata["Length"] = posn
    elif qstn_type == "Grid":
        colCnt = 0
        rowCnt = 0
        metadata["QuestionNo"] = qstn_posn - firstQstnInSection + 1
        end = len(metadataList)
        for x in range(end):
            value = metadataList[x]
            if value == "Subtitle":
                x += 1
                metadata["Subtitle"] = str(metadataList[x])
            elif value == "Column count":
                x += 1
                colCnt = int(metadataList[x])
                metadata["col-cnt"] = str(colCnt)
            elif value == "Row  count":
                x += 1
                rowCnt = int(metadataList[x])
                metadata["row-cnt"] = str(rowCnt)
            elif value == "Column Headings":
                colList = []
                for y in range(colCnt):
                    colList.append(str(metadataList[x+y+1]))
                metadata["columns"] = colList
                x += colCnt
            elif value == "Row Questions":
                rowList = []
                for y in range(rowCnt):
                    rowList.append(str(metadataList[x+y+1]))
                metadata["rows"] = rowList
                x += rowCnt
            elif value == "Question Type":
                rowList = []
                childType = []
                for y in xrange(x+1, end):
                    value = metadataList[y]
                    if  value == "GridChild":
                        break
                    else:
                        childType.append(str(value))
                if len(childType) == 1:
                    colList = childType*colCnt
                    rowList = [colList] * rowCnt
                    metadata["data"] = rowList
                elif len(childType) == colCnt:
                    for r in range(rowCnt):
                        rowList.append(childType)
                    metadata["data"] = rowList
                else:
                    for r in range(rowCnt):
                        colList = []
                        for c in range(colCnt):
                            colList.append(childType[r*colCnt + c])
                        rowList.append(colList)
                    metadata["data"] = rowList
                if  value == "GridChild":
                    if len(childType) == 1:
                        metadata.update(processGridChildMetadataAll(metadataList[y:], colCnt, rowCnt, qstn_code, qstn_posn, firstQstnInSection, childType))
                    elif len(childType) == colCnt:
                        metadata.update(processGridChildMetadataColumn(metadataList[y:], colCnt, rowCnt, qstn_code, qstn_posn, firstQstnInSection, childType))
                    else:
                        metadata.update(processGridChildMetadataElement(metadataList[y:], qstn_code, qstn_posn, firstQstnInSection, childType))
                break
        next_qstn_posn = qstn_posn + colCnt * rowCnt
    else:
        pass
    return (metadata, next_qstn_posn)

def getQstnMetadata(sheetQ, row, qstn_type, qstn_code, qstn_posn, firstQstnInSection):
    metadataList = []
    for col in xrange(5,sheetQ.ncols):
        value = sheetQ.cell_value(row, col)
        if value == "":
            break
        metadataList.append(value)
    (metadata, qstn_posn) = processMetadata(metadataList, qstn_type, qstn_code, qstn_posn, firstQstnInSection)
    return (metadata, qstn_posn)

def formatQuestionnaire(sheetQ, templateDetails, sections):
    questionnaire = []
    questions = []
    theSection = ""
    sectionPosn = 0
    firstQstnInSection = 0
    next_qstn_posn = 1
    line = []
    for row in range(sheetQ.nrows):
        qstn_posn = next_qstn_posn
        line = templateDetails[:]
        qstn_code = sheetQ.cell_value(row, 0)
        section = sheetQ.cell_value(row, 1)
        if section != theSection:
            theSection = section
            sectionPosn += 1
            firstQstnInSection = qstn_posn
        question = sheetQ.cell_value(row, 2)
        qstn_type = sheetQ.cell_value(row, 3)
        qstn_notes = sheetQ.cell_value(row, 4)
        (metadata, next_qstn_posn) = getQstnMetadata(sheetQ, row, qstn_type, qstn_code, qstn_posn, firstQstnInSection)
        questions.append(qstn_code)
        line.append(section)
        line.append(sectionPosn)
        line.append(question)
        line.append(qstn_type)
        line.append(qstn_notes)
        line.append(qstn_posn)
        line.append(qstn_code)
        if metadata != {}:
            line.append(metadata)
        questionnaire.append(line)
    return (questions, questionnaire)

def processColumns(sheetL, questions, rowStart, rowEnd):
    columns = []
    for col in xrange(1,sheetL.ncols):
        colList = []
        for row in xrange(rowStart, rowEnd):
            value = sheetL.cell_value(row, col)
            if value == "":
                break
            if value in questions:
                colList.append(str(value))
                layoutQuestions.append(value)
            else:
                colList.append(processLabel(value))
        if colList == []:
            break
        columns.append(colList)
    return [{'columns':columns}]
    
def processRow(sheetL, questions, row):
    rowList = []
    for col in range(sheetL.ncols):
        value = sheetL.cell_value(row, col)
        if value in questions:
            rowList.append(str(value))
            layoutQuestions.append(value)
    return rowList

def processLabel(value):
    return {'heading':str(value)}

def getLayoutRules(sheetL, questions, rowStart, rowEnd):
    colStart = None
    rules = []
    for row in xrange(rowStart, rowEnd):
        value = sheetL.cell_value(row, 0)
        if value == "columns":
            if colStart != None:
                rules.append(processColumns(sheetL, questions, colStart, row))
            colStart = row
        elif value == "":
            pass
        elif value in questions:
            if colStart != None:
                rules.append(processColumns(sheetL, questions, colStart, row))
                colStart = None
            rules.append(processRow(sheetL, questions, row))
        else:
            rules.append(processLabel(value))
    if colStart != None:
        rules.append(processColumns(sheetL, questions, colStart, rowEnd))
    return rules

def formatLayout(sheetL, template, sections, questions):
    layoutMethod = 1
    layout = []
    sectionLength = len(sections)
    rowStart = rowEnd = 0
    rowLimit = sheetL.nrows
    for i in range(sectionLength):
        section = sections[i]
        while rowStart < rowLimit:
            if sheetL.cell_value(rowStart, 0) == section:
                break
            else:
                rowStart += 1
        if i+1 == sectionLength:
            rowEnd = rowLimit
        else:
            nextSection = sections[i+1]
            while rowEnd < rowLimit:
                if sheetL.cell_value(rowEnd, 0) == nextSection:
                    break
                else:
                    rowEnd += 1
        rule = repr(getLayoutRules(sheetL, questions, rowStart+1, rowEnd))
        layout.append([template,section,i+1,layoutMethod,rule])
    return layout

def loadSpreadsheet(name):
    workbook = xlrd.open_workbook(filename=name)
    sheetT = workbook.sheet_by_name("Template")
    sheetS = workbook.sheet_by_name("Sections")
    sheetQ = workbook.sheet_by_name("Questions")
    sheetL = workbook.sheet_by_name("Layout")
    templateDetails = []
    for row in xrange(0, sheetT.nrows):
        templateDetails.append(sheetT.cell_value(row, 0))
    sections = []
    for row in xrange(0, sheetS.nrows):
        sections.append(sheetS.cell_value(row, 0))
    (questions, questionnaire) = formatQuestionnaire(sheetQ, templateDetails, sections)
    layout = formatLayout(sheetL, templateDetails[0], sections, questions)
    
    # Report back the questions that are not in the layout
    missing = []
    for qstn in questions:
        if qstn not in layoutQuestions:
            missing.append(qstn)
    if missing != []:
        print "The following questions are missing from the layout: %s" % missing
    

    return (questionnaire, layout)

def generateQuestionnaireCSV(name, questionnaire):
    csvName = "%s.Question.csv" % name
    headings = ["Template","Template Description","Complete Question","Date Question","Time Question","Location Question","Priority Question","Section","Section Position","Question","Question Type","Question Notes","Question Position","Question Code","Meta Data"]
    writer = csv.writer(open(csvName, "w"))
    writer.writerows([headings])
    writer.writerows(questionnaire)
    pass

def generateLayoutCSV(name, layout):
    csvName = "%s.Layout.csv" % name
    headings = ["Template","Section","Posn","Method","Rules"]
    writer = csv.writer(open(csvName, "w"))
    writer.writerows([headings])
    writer.writerows(layout)

def _main():
    """
    Parse arguments and run checks generate the csv files
    """
    if len(sys.argv) == 1:
        print "Please add a spreadsheet to process"
        return

    spreadsheetName = sys.argv[1]
    (questionnaire, layout) = loadSpreadsheet(spreadsheetName)
    generateQuestionnaireCSV(spreadsheetName, questionnaire)
    generateLayoutCSV(spreadsheetName, layout)

if __name__ == '__main__':
    _main()

