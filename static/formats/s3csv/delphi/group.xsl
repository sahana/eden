<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Delphi Group - CSV Import Stylesheet

         - use for import to delphi/group resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be delphi/group/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Name....................delphi_group
         Description.............delphi_group

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

        <xsl:variable name="GroupName" select="col[@field='Name']/text()"/>

        <!-- Create the Group -->
        <resource name="delphi_group">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$GroupName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$GroupName"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
