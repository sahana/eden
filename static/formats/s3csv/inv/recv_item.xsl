<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Inventory Receive Item - CSV Import Stylesheet

         - use for import to /inv/recv_item/create resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be inv/recv_item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors

         CSV fields:
         warehouse..............inv_recv.site_id -> org_office.name
         eta....................inv_recv.eta
         date...................inv_recv.date
         type...................inv_recv.type
         recipient..............unused (will change to human resource)
         from_location..........inv_recv.from_location_id -> gis_location.name
         organisation...........inv_recv.organisation_id -> org_organisation.name
         sender.................unused (will change to human resource)
         status.................inv_recv.status
         inv_recv.comments......inv_recv.comments
         item...................inv_recv_item.item_id -> supply_item.name
         item_pack..............inv_recv_item.item_id -> supply_item.name
         quantity...............inv_recv_item.quantity
         request................inv_recv_item.req_id -> req_req.request_number
         inv_recv_item.comments.inv_recv_item.comments

    *********************************************************************** -->

</xsl:stylesheet>