<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Tour Details - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be tour/details/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Code............................tour_config.code
         Posn............................tour_details.posn
         Controller......................tour_details.controller
         Function........................tour_details.function
         Args............................tour_details.args
         Tip_Title.......................tour_details.tip_title
         Tip_Details.....................tour_details.tip_details
         HTML_ID.........................tour_details.html_id
         HTML_Class......................tour_details.html_class
         Button..........................tour_details.button
         Tip_Location....................tour_details.tip_location
         DataTable_ID....................tour_details.datatable_id
         DataTable_row...................tour_details.datatable_row
         Redirect........................tour_details.redirect


    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Tour Config -->
        <xsl:variable name="Code"><xsl:value-of select="col[@field='Code']"/></xsl:variable>
        <resource name="tour_config">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Code"/>
            </xsl:attribute>
            <data field="code"><xsl:value-of select="$Code"/></data>
        </resource>

        <!-- Tour Details -->
        <resource name="tour_details">
            <reference field="tour_config_id" resource="tour_config">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Code"/>
                </xsl:attribute>
            </reference>
            <data field="posn"><xsl:value-of select="col[@field='Posn']"/></data>
            <data field="controller"><xsl:value-of select="col[@field='Controller']"/></data>
            <data field="function"><xsl:value-of select="col[@field='Function']"/></data>
            <data field="args"><xsl:value-of select="col[@field='Args']"/></data>
            <data field="tip_title"><xsl:value-of select="col[@field='Tip_Title']"/></data>
            <data field="tip_details"><xsl:value-of select="col[@field='Tip_Details']"/></data>
            <data field="html_id"><xsl:value-of select="col[@field='HTML_ID']"/></data>
            <data field="html_class"><xsl:value-of select="col[@field='HTML_Class']"/></data>
            <data field="button"><xsl:value-of select="col[@field='Button']"/></data>
            <data field="tip_location"><xsl:value-of select="col[@field='Tip_Location']"/></data>
            <data field="datatable_id"><xsl:value-of select="col[@field='DataTable_ID']"/></data>
            <data field="datatable_row"><xsl:value-of select="col[@field='DataTable_row']"/></data>
            <data field="redirect"><xsl:value-of select="col[@field='Redirect']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
