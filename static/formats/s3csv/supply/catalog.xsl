<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Catalogs - CSV Import Stylesheet

         CSV fields:
         Catalog.........................supply_catalog.name
         Organisation....................supply_catalog.organisation_id$name
         Comments........................supply_catalog.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations',
                                                                   col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Catalogues -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="supply_catalog">

            <data field="name"><xsl:value-of select="col[@field='Catalog']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <xsl:if test="$OrgName!=''">
                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Organisation:', $OrgName)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

        </resource>
        
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$OrgName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Organisation:', $OrgName)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
