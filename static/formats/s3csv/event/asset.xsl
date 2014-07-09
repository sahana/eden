<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Event Assets - CSV Import Stylesheet
         - useful for Demos/Simulations

         CSV column...........Format..........Content

         Incident.............string..........Incident Name
         Asset................string..........Asset Number
         Status...............string..........Status

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../commons.xsl"/>

    <xsl:variable name="IncidentPrefix" select="'Incident:'"/>
    <xsl:variable name="AssetPrefix" select="'Asset:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="incident" match="row" use="col[@field='Incident']"/>
    <xsl:key name="asset" match="row" use="col[@field='Asset']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Incidents -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('incident',
                                                                   col[@field='Incident'])[1])]">
                <xsl:call-template name="Incident" />
            </xsl:for-each>

            <!-- Assets -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('asset',
                                                                   col[@field='Asset'])[1])]">
                <xsl:call-template name="Asset" />
            </xsl:for-each>

            <!-- Links -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        <xsl:variable name="Incident">
            <xsl:value-of select="col[@field='Incident']"/>
        </xsl:variable>
        <xsl:variable name="Asset">
            <xsl:value-of select="col[@field='Asset']"/>
        </xsl:variable>
        <xsl:variable name="Status">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Status']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="event_asset">

            <!-- Link to Incident -->
            <reference field="incident_id" resource="event_incident">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($IncidentPrefix, $Incident)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Asset -->
            <reference field="asset_id" resource="asset_asset">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($AssetPrefix, $Asset)"/>
                </xsl:attribute>
            </reference>

            <xsl:choose>
                <xsl:when test="$Status=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Status='ALERTED'">
                    <data field="status">1</data>
                </xsl:when>
                <xsl:when test="$Status='STANDING BY'">
                    <data field="status">2</data>
                </xsl:when>
                <xsl:when test="$Status='ACTIVE'">
                    <data field="status">3</data>
                </xsl:when>
                <xsl:when test="$Status='DEACTIVATED'">
                    <data field="status">4</data>
                </xsl:when>
                <xsl:when test="$Status='UNABLE'">
                    <data field="status">5</data>
                </xsl:when>
            </xsl:choose>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Incident">

        <xsl:variable name="IncidentName" select="col[@field='Incident']/text()"/>

        <xsl:if test="$IncidentName!=''">
            <resource name="event_incident">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($IncidentPrefix, $IncidentName)"/>
                </xsl:attribute>

                <data field="name"><xsl:value-of select="$IncidentName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Asset">

        <xsl:variable name="AssetName" select="col[@field='Asset']/text()"/>

        <xsl:if test="$AssetName!=''">
            <resource name="asset_asset">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($AssetPrefix, $AssetName)"/>
                </xsl:attribute>

                <data field="number"><xsl:value-of select="$AssetName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
