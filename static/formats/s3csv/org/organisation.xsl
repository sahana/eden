<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Organisation - CSV Import Stylesheet

         2011-Jun-13 / Graeme Foster <graeme AT acm DOT org>

         - use for import to org/organisation resource
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
         Name....................org_organisation
         Acronym.................org_organisation
         Type....................org_organisation
         Sector..................org_sector
         Region..................org_organisation
         Country.................org_organisation (ISO Code)
         Website.................org_organisation
         Twitter.................org_organisation
         Donation Phone..........org_organisation
         Comments................org_organisation

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/countries.xsl"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- Organisation types, see models/05_org.py -->
    <org:type code="1">Government</org:type>
    <org:type code="2">Embassy</org:type>
    <org:type code="3">International NGO</org:type>
    <org:type code="4">Donor</org:type>
    <org:type code="6">National NGO</org:type>
    <org:type code="7">UN</org:type>
    <org:type code="8">International Organization</org:type>
    <org:type code="9">Military</org:type>
    <org:type code="10">Private</org:type>
    <org:type code="11">Intergovernmental Organization</org:type>
    <org:type code="12">Institution</org:type>
    <org:type code="13">Red Cross / Red Crescent</org:type>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the sectors -->
        <xsl:variable name="sector" select="col[@field='Sector']"/>
        <xsl:call-template name="splitList">
            <xsl:with-param name="list" select="$sector"/>
        </xsl:call-template>

        <!-- Create the Organisation -->
        <resource name="org_organisation">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>

            <xsl:variable name="typename" select="col[@field='Type']"/>
            <xsl:variable name="typecode" select="document('')//org:type[text()=normalize-space($typename)]/@code"/>
            <xsl:if test="$typecode">
                <data field="type"><xsl:value-of select="$typecode"/></data>
            </xsl:if>

            <data field="country">
                <xsl:value-of select="col[@field='Country']"/>
                <!--<xsl:call-template name="iso2countryname">
                    <xsl:with-param name="country" select="col[@field='country']"/>
                </xsl:call-template>-->
            </data>
            <data field="region"><xsl:value-of select="col[@field='Region']"/></data>
            <data field="website"><xsl:value-of select="col[@field='Website']"/></data>
            <data field="twitter"><xsl:value-of select="col[@field='Twitter']"/></data>
            <data field="donation_phone"><xsl:value-of select="col[@field='Donation Phone']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <reference field="sector_id" resource="org_sector">
                <xsl:variable name="qlist">
                    <xsl:call-template name="quoteList">
                        <xsl:with-param name="list" select="$sector"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('[', $qlist, ']')"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template to create an org_sector resource from the value passed in -->
    <xsl:template name="resource">
        <xsl:param name="item"/>

        <resource name="org_sector">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item"/>
            </xsl:attribute>
            <data field="abrv"><xsl:value-of select="$item"/></data>
            <data field="name"><xsl:value-of select="$item"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
