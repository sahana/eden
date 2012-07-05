# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__doc__ = "Module to spawn modem connectivity"

__author__ = "Praneeth Bodduluri <lifeeth[at]gmail.com>"

import sys, os
path = os.path.join(request.folder, "modules")
if not path in sys.path:
    sys.path.append(path)
import pygsm
import threading
import time
from pygsm.autogsmmodem import GsmModemNotFound
import s3msg

class ModemThread( threading.Thread ):
    def __init__(self, modem):
        self.modem = modem
        threading.Thread.__init__ ( self )
        self.msg = s3msg.S3Msg(globals(), deployment_settings, db, modem=modem)

    def run(self):
        boxdata = self.modem.query("AT+CMGD=?")
        boxsize = int(boxdata.split("(")[1].split(")")[0].split("-")[1])
        cleanup = False
        while True:
            self.msg.process_outbox(contact_method="SMS")
            for i in range(5):
                # parse 5 messages in one shot
                message = self.modem.next_message()
                if message is not None:
                    cleanup = True
                    # for debug purposes
                    #print "Got message: " + message.text
                    # Temp: SMS AutoResponder on by default
                    #self.modem.send_sms(message.sender, "This is to be replaced with the autorespond message")
                    self.msg.receive_msg(message=message.text, fromaddress=message.sender, pr_message_method="SMS")
                if cleanup:
                    for i in range(boxsize): # For cleaning up read messages.
                        try:
                            temp = self.modem.command("AT+CMGR=" + str(i+1) + ",1")
                            if "REC READ" in temp[0]:
                                self.modem.query("AT+CMGD=" + str(i+1))
                        except:
                            pass
                    cleanup = False
            time.sleep(5)
		#self.modem.send_sms("9935648569", "Hey!")

s3db.table("msg_modem_settings")
modem_configs = db(db.msg_modem_settings.enabled == True).select()

# PyGSM GsmModem class instances
modems = []

for modem in modem_configs:
    # mode is set to text as PDU mode is flaky
    modems.append(pygsm.GsmModem(port=modem.modem_port, baudrate=modem.modem_baud, mode="text"))

if len(modems) == 0:
    # If no modem is found try autoconfiguring - We shouldn't do this anymore
    #try:
    #  modems.append(pygsm.AutoGsmModem())
    #except GsmModemNotFound, e:
    #  # No way yet to pass back the error yet
    #  pass
    pass
else:
    # Starting a thread for each modem we have
    for modem in modems:
        ModemThread(modem).run()
