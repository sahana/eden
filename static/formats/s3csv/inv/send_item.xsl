<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Inventory Receive Item - CSV Import Stylesheet

         - use for import to /inv/send_item/create resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be inv/send_item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors

         CSV fields:
         warehouse..............inv_send.site_id -> org_office.name
         sender.................unused (will change to human resource)
         date...................inv_send.date
         delivery_date..........inv_send.delivery_date
         to_site_id.............inv_send.to_site_id
         status.................inv_send.status
         recipient..............unused (will change to human resource)
         inv_send.comments......inv_send.comments
         item...................inv_send_item.item_id -> supply_item.name
         item_pack..............inv_send_item.item_id -> supply_item.name
         quantity...............inv_send_item.quantity
         request................inv_send_item.req_id -> req_req.request_number
         inv_send_item.comments.inv_send_item.comments

    *********************************************************************** -->

</xsl:stylesheet>