<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Scenario Assets - CSV Import Stylesheet

         CSV fields:
         Scenario................event_scenario_asset.scenario_id$name
         Item....................event_scenario_asset.item_id$name
         Comments................event_scenario_asset.comments

    *********************************************************************** -->
    
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="scenarios" match="row" use="col[@field='Scenario']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Scenarios -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('scenarios', col[@field='Scenario'])[1])]">
                <xsl:call-template name="Scenario"/>
            </xsl:for-each>

            <!-- Scenario Assets -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="event_scenario_asset">

            <!-- Link to Scenario -->
            <reference field="scenario_id" resource="event_scenario">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Scenario']"/>
                </xsl:attribute>
            </reference>

            <!-- Item -->
            <reference field="item_id" resource="supply_item">
                <resource name="supply_item">
                    <data field="name"><xsl:value-of select="col[@field='Item']"/></data>
                </resource>
            </reference>

            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Scenario">

        <xsl:variable name="ScenarioName" select="col[@field='Scenario']/text()"/>

        <resource name="event_scenario">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ScenarioName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ScenarioName"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
