import unittest, time
from selenium import selenium

class Form(unittest.TestCase):
    def __init__ (self, action):
        self.action = action
        self.sel = action.sel

    def fillForm(self, id, value, type="text"):
        """
            Method to fill an element in a form
        """
        sel = self.sel
        if type=="text":
            sel.type(id,value)
        elif type == "select":
            sel.select(id, value)
        return self

    def fillSelect(self, id, value):
        """
            Method to fill a select drop down in a form
        """
        self.sel.select(id, value)
        return self

    def fillAutoComplete(self, fieldID, value, throbber):
        sel = self.sel
        sel.type(fieldID,value)
        sel.fire_event(fieldID, "keydown")
        for i in range(60):
            automenu = 0 
            while sel.is_element_present("//ul[@id='ui-menu-%s']" % automenu):
                autoitem = 0
                locator = "//a[@id='ui-menu-%s-%s']" % (automenu, autoitem)
                while sel.is_element_present(locator):
                    linkText = sel.get_text(locator)
                    #print "Looking for %s found %s" %(value, linkText)
                    if value in linkText:
                        sel.mouse_over(locator)
                        sel.click(locator)
                        # wait for throbber to close
                        time.sleep(1)
                        if throbber == None:
                            return
                        locator = "//img[@id='%s']" % throbber
                        giveup = 0
                        while sel.is_visible(locator):
                            time.sleep(1)
                            giveup += 1
                            if giveup == 20:
                                return
                        return;
                    autoitem += 1
                    locator = "//a[@id='ui-menu-%s-%s']" % (automenu, autoitem)
                automenu += 1
            time.sleep(1)
        print "Unable to select %s" % value
        self.assertTrue(False)

    def saveForm(self, submit, message=None, success=True):
        """
            Method to save the details
            @param message: the success message to check (optional)
            @param success: whether we're looking for a confirmation (default) or failure
        """
        sel = self.sel
        sel.click("//input[@value='%s']" % submit)
        sel.wait_for_page_to_load("30000")
        if message != None:
            if success:
                return self.action.successMsg(message)
            else:
                return self.action.errorMsg(message)
        return True

    def getFormElements(self, formName=None):
        """
            Method that will return a list of the elements in the form
            The list will consist of the element type, followed by the id
            Except for a submit button in which case it will be the value
        """
        sel = self.sel
        elements = []
        i = 0
        cont = True
        while cont:
            i += 1
            if formName == None:
                partid = "//form//tr[%s]" % i
            else:
                partid = "//form[@id='%s']//tr[%s]" %(formName, i)
            if sel.is_element_present(partid):
                # Cater for multiple input elements embedded in the same table row
                # These occur in the autocomplete widgets
                j = 0
                jGo = True
                while jGo:
                    j += 1
                    elementid = partid + "//input[%s]" %j
                    if sel.is_element_present(elementid):
                        type = sel.get_attribute(elementid+"@type")
                        if type == 'submit':
                            elements.append((type, "submit-"+sel.get_attribute(elementid+"@value")))
                        else:
                            elements.append((type, sel.get_attribute(elementid+"@id")))
                        continue
                    else:
                        jGo = False
                elementid = partid + "//select"
                if sel.is_element_present(elementid):
                    elements.append(("select", sel.get_attribute(elementid+"@id")))
                    continue
                elementid = partid + "//textarea"
                if sel.is_element_present(elementid):
                    elements.append(("textarea", sel.get_attribute(elementid+"@id")))
                    continue
            else: # No more table rows exist
                cont = False
        return elements
    
    def checkForm(self, formTemplate, readonly=False):
        # Method to to check the layout of a form
        formTemplate.checkElements(readonly)
        elements = formTemplate.elementsSucess
        failed = formTemplate.elementsfailed
        if len(failed) > 0:
            msg = '\n'.join(failed)
            self.fail(msg)
        if len(elements) > 0:
            print "Verified the following form elements:"
            for element in elements: print"\t%s" % element

    def checkFormStrict(self, formTemplate, formName=None):
        errorList = []
        templateList = []
        for element in formTemplate.elementList:
            if element.tag() != 'label':
                templateList.append(unicode(element.key()))

        elementList = self.getFormElements(formName)
        for element in elementList:
            cnt = 0
            found = False
            for template in templateList:
                if element[1] == template:
                    del templateList[cnt]
                    found = True
                    break
                cnt += 1
            if not found:
                errorList.append("%s displayed but not in template"%element[1])

        for template in templateList:
            errorList.append("%s in template but not displayed"%template)
        return errorList
    
class FormTemplate(unittest.TestCase):
    def __init__(self, action):
        self.elementList = []
        self.action = action
        self.sel = action.sel

    def addFormElement(self,
                       id=None,
                       tag=None,
                       type=None,
                       visible=None,
                       value=None,
                       elementDetails=()
                       ):
        """
            The method can be called with either individual arguments or the
            arguments in a list
            However it is called:
            either the id is required
            or if the type is submit then a value is required.
            
            The elementDetails parameter is a list of up to 5 elements
            elementDetails[0] the id associated with the HTML tag
            elementDetails[1] the HTML tag [input, select]
            elementDetails[2] *optional* the type of input tag [checkbox, password, radio, text]
            elementDetails[3] *optional* the visibility of the HTML tag
            elementDetails[4] *optional* the value or text of the HTML tag
            
            If the element already exists in the list then the data will be
            modified, otherwise it will be treated as an insert.
            For an insert if no tag is provided it will be defaulted to an
            input with type text.
            A newly created element will default to being visible.
        """
        if len(elementDetails) >0:
            id = elementDetails[0]
            if len(elementDetails) >1:
                tag = elementDetails[1]
                if len(elementDetails) >2:
                    type = elementDetails[2]
                    if len(elementDetails) >3:
                        visible = elementDetails[3]
                        if len(elementDetails) >4:
                            value = elementDetails[4]
        element = self.getElementFromKey(id, type, value)
        if id != None: element.setId(id)
        if tag != None: element.setTag(tag)
        if type != None: element.setType(type)
        if visible != None: element.setVisible(visible)
        if value != None: element.setValue(value)
        return element

    def removeElement(self, id):
        for elementObj in self.elementList:
            if elementObj.id() == id:
                self.elementList.remove(elementObj)
                return
        
    def addInput(self,
                 inputID,
                 type=None,
                 labelID=None,
                 labelText=None,
                 value=None,
                 visible=None
                 ):
        elObj = self.addFormElement(inputID, "input", type, visible, value)
        if labelID != None:
            elObj.setLabelID(labelID)
        if labelText != None:
            elObj.setLabelText(labelText)
        return elObj
        
    def addSelect(self, selectID, labelID=None, value=None, visible=None, labelText=None):
        elObj = self.addFormElement(id=selectID,
                                    tag="select",
                                    visible=visible,
                                    value=value
                                    )
        if labelID != None:
            elObj.setLabelID(labelID)
        if labelText != None:
            elObj.setLabelText(labelText)
        return elObj
            
    def addTextArea(self, textID, labelID=None, value=None, visible=None, labelText=None):
        elObj = self.addFormElement(id=textID,
                                    tag="textarea",
                                    visible=visible,
                                    value=value
                                    )
        if labelID != None:
            elObj.setLabelID(labelID)
        if labelText != None:
            elObj.setLabelText(labelText)
        return elObj
            
    def addButton(self, value, visible=None):
        elObj = self.addFormElement(tag="input",
                                    type="submit",
                                    visible=visible,
                                    value=value
                                    )
        return elObj
        
    def showElement(self, elementId):
        """
            Method to set an element to be visible
        """
        self.startCoverage("showElement")
        self.getElementFromKey(value).setVisible(True)
        self.endCoverage()
        return self
        
    def hideElement(self, elementDetails):
        """
            Method to set an element to be hidden
        """
        self.startCoverage("hideElement")
        self.getElementFromKey(value).setVisible(False)
        self.endCoverage()
        return self
        
    def getElementFromKey(self, id=None, type=None, value=None):
        if id==None:
            key = "%s-%s" % (type, value)
        else:
            key = id
        for obj in self.elementList:
            if obj.key() == key:
                return obj
        obj = ElementDetail(key=key, visible=True, tag="input", type="text")
        self.elementList.append(obj)
        return obj
    
    def checkElements(self, readonly):
        self.elementsSucess = []
        self.elementsfailed = []
        for elementObj in self.elementList:
            result = elementObj.checkElement(self.sel, readonly)
            if result == True:
                self.elementsSucess.append(elementObj.checkStatus(readonly))
            elif result == "Ignored":
                pass
            else: self.elementsfailed.append(result)
                    
    def checkForm(self, readonly=False):
        return self.action.checkForm(self, readonly)
        
    def checkFormStrict(self, formName=None):
        return self.action.checkFormStrict(self, formName)

    def addDataToTemplate(self, dataDict, idPrefix):
        """
            This attempts to add data to the elementList
            it can only do this if the key in the dataDict matches the
            value in the elementList 
        """
        for (key, value) in dataDict.items():
            key = "%s_%s" % (idPrefix, key)
            for obj in self.elementList:
                if obj.key() == key:
                    obj.setValue(value)
                    break

    def removeDataFromTemplate(self):
        """
            This will remove all data values in the elementList
        """
        for obj in self.elementList:
            obj.setValue(None)

class ElementDetail():
    def __init__(self,
                 key,
                 id=None,
                 tag=None,
                 type=None,
                 visible=True,
                 value=None,
                 labelID=None,
                 labelText=None,
                 balloonTitle=None,
                 balloonText=None
                 ):
        self._key = key
        self._id = id
        self._tag = tag
        self._type = type
        self._visible = visible
        self._value = value
        self._labelID = labelID
        self._labelText = labelText
        self._balloonTitle = balloonTitle
        self._balloonText = balloonText

    def key(self): return self._key
    def id(self): return self._id
    def tag(self): return self._tag
    def type(self): return self._type
    def visible(self):return self._visible
    def value(self): return self._value
    def labelID(self): return self._labelID
    def labelText(self): return self._labelText
    def balloonTitle(self): return self._balloonTitle
    def balloonText(self): return self._balloonText
    
    def checkStatus(self, readonly):
        status = self._key
        if readonly:
            if self._visible and self._value != None: status += " readonly value"
            if self._labelID != None: status += " with label"
        else:
            if self._visible: status += " visible"
            if self._labelID != None: status += " with label"
            if self._balloonTitle != None: status += " with balloon help"
            if self._value != None: status += " with value"
        return status

    def setId(self,id):
        self._id = id
        return self
    
    def setTag(self,tag):
        self._tag = tag
        return self
    
    def setType(self,type):
        self._type = type
        return self
    
    def setVisible(self,visible):
        self._visible = visible
        return self
    
    def setHide(self):
        self._visible = False
        return self

    def setShow(self):
        self._visible = True
        return self
    
    def setValue(self,value):
        self._value = value
        return self
    
    def setLabelID(self, labelID):
        self._labelID = labelID
        return self
    
    def setLabelText(self, labelText):
        self._labelText = labelText
        return self
    
    def setBalloonTitle(self, balloonTitle):
        self._balloonTitle = balloonTitle
        return self
    
    def setBalloonText(self, balloonText):
        self._balloonText = balloonText
        return self
    

    def checkElement(self, sel, readonly):
        """
            Method to check that form _element is present
            return True on success error message on failure
        """
        if readonly:
            if self._type == "submit":
                return "Ignored"
            searchString = '//tr[@id="%s__row"]' % self._id
        elif self._id == None:
            searchString = '//input[@value="%s"]' % self._value
        else:
            searchString = '//%s[@id="%s"]' % (self._tag, self._id)
        msg = ""
        if sel.is_element_present(searchString):
            # only check for visibility if the element hasn't been disabled
            if sel.is_editable(searchString) \
            and (sel.is_visible(searchString) != self._visible):
                msg += "%s element %s doesn't have a visibility of %s" % (self._tag, self._key, self._visible)
        else:
            return "%s element %s doesn't exist on the form" % (self._tag, self._key)
        if self._visible:
            if readonly:
                if self._labelID != None:
                    if not sel.is_element_present('//label[@id="%s"]'%self._labelID):
                        msg += "label %s is missing" % self._labelID
                if self._value != None:
                    result = sel.get_text(searchString)
                    if self._value not in result:
                        msg += "text value %s is missing" % self._value
            else:
                if not sel.is_element_present(searchString):
                    msg += "%s element %s is missing" % (self._tag, self._key)
                if self._labelID != None:
                    if not sel.is_element_present('//label[@id="%s"]'%self._labelID):
                        msg += "label %s is missing" % self._labelID
                # Check the value held in the element
                # ignore any dummy element
                if not self._key.startswith("dummy"):
                    actual = sel.get_value(searchString)
                    #print "element %s [%s]: actual %s, expected %s" % (self._id, searchString, actual, self._value)
                    if actual != "" or self._value != None:
                        if self._value != actual:
                            if self._tag == "select":
                                if actual == "" or self._value != sel.get_selected_label(searchString):
                                    msg += "expected %s for element %s doesn't equal the actual value of %s" % (self._value, self._id, actual)
                            else:
                                msg += "expected %s for element %s doesn't equal the actual value of %s" % (self._value, self._id, actual)
                if self._balloonTitle != None:
                    result = self.checkBalloon(sel)
                    if result != True:
                        msg += result
        if msg != "": return msg
        return True
    
    def checkBalloon(self, sel):
        """
            Method to check that the help message is displayed
        """
        element = "//div[contains(@title,'%s')]" % (self._balloonTitle)
        if sel.is_element_present(element):
            sel.mouse_over(element)
            if sel.is_element_present(element):
                return "Help %s exists but is not displaying" % (self._balloonTitle)
            return True
        else:
            return "Help %s is missing" % (self._balloonTitle)

class rHeaderTemplate(unittest.TestCase):
    def __init__(self, action):
        self.headingList = []
        self.action = action
        self.sel = action.sel
        
    def addHeading(self, text):
        self.headingList.append(rHeadingElement(text))
        
    def addValue(self, heading, value):
        for textObj in self.headingList:
            if textObj.getHeading() == heading:
                textObj.setValue(value)
                return
        self.headingList.append(rHeadingElement(heading, value))
        
    def checkrHeader(self):
        sel = self.sel
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        searchString = ""
        for textObj in self.headingList:
            msg = "Unable to find details of %s in the header of %s"
            self.assertTrue(textObj.getHeading() in heading, msg % (textObj.getHeading(), heading))
            self.assertTrue(textObj.getValue() in heading, msg % (textObj.getValue(), heading))
        print "Verified the following rHeader elements:"
        for textObj in self.headingList:
            print"\t%s\t%s" % (textObj.getHeading(), textObj.getValue())

class rHeadingElement():
    def __init__(self, heading, value=None):
        self._heading = heading
        self._value = value
        
    def getHeading(self):
        return self._heading
    def getValue(self):
        return self._value
    
    def setHeading(self, heading):
        self._heading = heading
    def setvalue(self, value):
        self._value = value
