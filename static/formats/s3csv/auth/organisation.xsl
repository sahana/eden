<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Auth Organisation - CSV Import Stylesheet

         2011-Nov-09 / Fran Boon for IFRC

         - use for import to auth/organisation resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be auth/organisation/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Name....................org_organisation
         Acronym.................org_organisation
         Domain..................auth_organisation (for whitelisted registrations)

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

        <xsl:variable name="OrgName" select="col[@field='Name']/text()"/>
        <xsl:variable name="Domain" select="col[@field='Domain']/text()"/>

        <!-- Create the Organisation -->
        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
            <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>
        </resource>

        <!-- Create the Organisation Whitelist -->
        <xsl:if test="$Domain!=''">
            <resource name="auth_organisation">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
                <data field="domain"><xsl:value-of select="$Domain"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
