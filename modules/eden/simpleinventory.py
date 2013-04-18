# -*- coding: utf-8 -*-

""" Sahana Eden Inventory Model

    @copyright: 2009-2013 (c) Sahana Software Foundation
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

__all__ = ["S3WarehouseModel",
           "S3InventoryModel",
           "S3TrackingModel",
           "S3AdjustModel",
           "inv_tabs",
           "inv_rheader",
           "inv_rfooter",
           "inv_recv_crud_strings",
           "inv_recv_rheader",
           "inv_send_rheader",
           "inv_ship_status",
           "inv_tracking_status",
           "inv_adj_rheader",
           ]

import itertools

from gluon import *
from gluon.sqlhtml import RadioWidget
from gluon.storage import Storage

from ..s3 import *
from eden.layouts import S3AddResourceLink

SHIP_STATUS_IN_PROCESS = 0
SHIP_STATUS_RECEIVED   = 1
SHIP_STATUS_SENT       = 2
SHIP_STATUS_CANCEL     = 3
SHIP_STATUS_RETURNING  = 4

# To pass to global scope
inv_ship_status = {"IN_PROCESS" : SHIP_STATUS_IN_PROCESS,
                   "RECEIVED"   : SHIP_STATUS_RECEIVED,
                   "SENT"       : SHIP_STATUS_SENT,
                   "CANCEL"     : SHIP_STATUS_CANCEL,
                   "RETURNING"  : SHIP_STATUS_RETURNING,
                   }

T = current.T
shipment_status = {SHIP_STATUS_IN_PROCESS: T("In Process"),
                   SHIP_STATUS_RECEIVED:   T("Received"),
                   SHIP_STATUS_SENT:       T("Sent"),
                   SHIP_STATUS_CANCEL:     T("Canceled"),
                   SHIP_STATUS_RETURNING:  T("Returning"),
                   }

SHIP_DOC_PENDING  = 0
SHIP_DOC_COMPLETE = 1

TRACK_STATUS_UNKNOWN    = 0
TRACK_STATUS_PREPARING  = 1
TRACK_STATUS_TRANSIT    = 2
TRACK_STATUS_UNLOADING  = 3
TRACK_STATUS_ARRIVED    = 4
TRACK_STATUS_CANCELED   = 5
TRACK_STATUS_RETURNING  = 6

inv_tracking_status = {"UNKNOWN"    : TRACK_STATUS_UNKNOWN,
                       "IN_PROCESS" : TRACK_STATUS_PREPARING,
                       "SENT"       : TRACK_STATUS_TRANSIT,
                       "UNLOADING"  : TRACK_STATUS_UNLOADING,
                       "RECEIVED"   : TRACK_STATUS_ARRIVED,
                       "CANCEL"     : TRACK_STATUS_CANCELED,
                       "RETURNING"  : TRACK_STATUS_RETURNING,
                       }

tracking_status = {TRACK_STATUS_UNKNOWN   : T("Unknown"),
                   TRACK_STATUS_PREPARING : T("In Process"),
                   TRACK_STATUS_TRANSIT   : T("In transit"),
                   TRACK_STATUS_UNLOADING : T("Unloading"),
                   TRACK_STATUS_ARRIVED   : T("Arrived"),
                   TRACK_STATUS_CANCELED  : T("Cancelled"),
                   TRACK_STATUS_RETURNING : T("Returning"),
                   }

#itn_label = T("Item Source Tracking Number")
# Overwrite the label until we have a better way to do this
itn_label = T("CTN")

settings = current.deployment_settings
inv_item_status_opts = settings.get_inv_item_status()
send_type_opts = settings.get_inv_shipment_types()
send_type_opts.update(inv_item_status_opts)
send_type_opts.update(settings.get_inv_send_types())
recv_type_opts = settings.get_inv_shipment_types()
recv_type_opts.update(settings.get_inv_recv_types())

