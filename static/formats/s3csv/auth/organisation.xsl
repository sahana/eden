<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Auth Organisation - CSV Import Stylesheet

         CSV fields:
         Organisation............org_organisation.name
         Acronym.................org_organisation.acronym
         Domain..................auth_organisation.domain
         Approver................@ToDo

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

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
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
