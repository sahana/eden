from Tkinter import *
import tkSimpleDialog

class SelectTestWindow(tkSimpleDialog.Dialog):
    def __init__(self, parent, module, details):
        self.module = module
        self.details = details
        tkSimpleDialog.Dialog.__init__(self, parent)

    def body(self, parent):
        self.testList = []
        self.slectedList = []
        self.winfo_toplevel().title("%s test cases" % self.module)
        Label(parent, text="Watch this space...").grid(row =0)
        testPanel = Frame(parent, borderwidth=2, relief=SUNKEN)
        testPanel.grid(row=0, column=0, sticky=NSEW)
        self.testcasePanel(testPanel)

    def buttonbox(self):
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)

        box.pack()

    def toggleButton(self):
        i = 0
        for testcase in self.testcases:
            # Set the state of the testcase depending upon the checkbox 
            if self.checkboxModules[i].get() == 1:
                testcase["state"] = True
            else:
                testcase["state"] = False
            i += 1

    def testcasePanel(self, panel):
        Label(panel,
              text="Select the test cases that you would like to run.").pack(side=TOP,
                                                                             anchor=W)
        detailPanel = Frame(panel)
        detailPanel.pack(side=TOP, anchor=W, fill=X)
        self.checkboxModules = []
        i = 0
        self.testcases = self.details["tests"]
        for test in self.testcases:
            var = IntVar()
            chk = Checkbutton(detailPanel, text=test["name"], variable=var,
                              command=self.toggleButton)
            if test["state"]:
                chk.select()
            self.checkboxModules.append(var)
            chk.grid(row=i//2, column=i%2*2, sticky=NW)
            i += 1
