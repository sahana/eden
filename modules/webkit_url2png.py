#!/usr/bin/env python

import sys
import signal

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebPage

def save_webpage_screenshot(url, width, height, file_name = None):
    """Saves a screenshot of the webpage given in url into filename+".png"
    
    width and height, if given, are in pixels
    if not given, the browser's default dimensions will be used.
    
    Needs a call to window.print() from within the webpage.
    
    Example:
    
    save_webpage_screenshot(
        "http://www.example.com",
        "example",
        width=1024,
        height=768
    )
    """
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    class MyQWebPage(QWebPage):
        @pyqtSlot()
        def shouldInterruptJavaScript(qwebpage):
            print "not interrupting"
            return False
        
    webpage = MyQWebPage()

    # set page dimensions
    webpage.setViewportSize(QSize(int(width), int(height)))

    # display errors otherwise debugging is very difficult
    def print_error(
        message,
        lineNumber,
        sourceID
    ):
        print "\n%(sourceID)s line %(lineNumber)i: \n  %(message)s" % locals()
    webpage.javaScriptConsoleMessage = print_error
    
    if file_name is None:
        result = []
        
    # register print request handler
    def onPrintRequested(virtual_browser_window):
        #print "onPrintRequested"

        # Paint this frame into an image
        image = QImage(
            webpage.viewportSize(),
            QImage.Format_ARGB32
        )
        painter = QPainter(image)
        virtual_browser_window.render(painter)
        painter.end()
        
        if file_name is not None:
            image.save(file_name)
        else:
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            result.append(str(byte_array))
            
        if __name__ == "__main__":
            if file_name is None:
                sys.stdout.write(result[0])
            sys.exit(0)
        else:
            app.quit()

    webpage.printRequested.connect(onPrintRequested)
    
    # load the page and wait for a print request
    webpage.mainFrame().load(QUrl(url))

    app.exec_()
    if file_name is None:
        return result[0]

if __name__ == "__main__":
    
    sys.exit(
        save_webpage_screenshot(
            *sys.argv[1:]
        )
    )