<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Location - CSV Import Stylesheet

         2011-Jun-13 / Graeme Foster <graeme AT acm DOT org>

         - use for import to gis/location resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be org/organisation/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Name....................gis_location.name
         Level...................gis_location.level      (optional)
         Parent..................gis_location.parent     (optional)
         Lat.....................gis_location.lat
         Lon.....................gis_location.lon
         Elevation...............gis_location.elevation  (optional)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="parents" match="row" use="col[@field='Parent']/text()"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Parent locations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('parents',
                                                        col[@field='Parent']/text())[1])]">
                <resource name="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Parent']"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='Parent']"/></data>
                </resource>
            </xsl:for-each>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="parent" select="col[@field='Parent']/text()"/>

        <!-- Create the gis location -->
        <resource name="gis_location">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            <xsl:if test="col[@field='Level']!=''">
                <data field="level"><xsl:value-of select="col[@field='Level']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Elevation']!=''">
                <data field="elevation"><xsl:value-of select="col[@field='Elevation']"/></data>
            </xsl:if>
            <xsl:if test="$parent!=''">
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$parent"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
