<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CMS Post - CSV Import Stylesheet

         - use for import to delphi/problem resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be delphi/problem/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Series...................Series Name (optional)
         Name.....................Post Name
         Body.....................Post Body (HTML)
         Module...................Post Module
         Roles....................Post Roles (not yet implemented)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="series" match="row" use="col[@field='Series']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Series -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('series',
                                                                   col[@field='Series'])[1])]">
                <xsl:call-template name="Series"/>
            </xsl:for-each>

            <!-- Posts -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Series" select="col[@field='Series']/text()"/>
        <xsl:variable name="Module" select="col[@field='Module']/text()"/>

        <resource name="cms_post">
            <xsl:if test="$Series!=''">
                <reference field="series_id" resource="cms_series">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Series"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$Module!=''">
                <data field="module"><xsl:value-of select="$Module"/></data>
            </xsl:if>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="body"><xsl:value-of select="col[@field='Body']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Series">
        <xsl:variable name="Series" select="col[@field='Series']/text()"/>

        <resource name="cms_series">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Series"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Series"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
