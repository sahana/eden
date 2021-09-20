<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Scenario Organisations - CSV Import Stylesheet

         CSV fields:
         Scenario................event_scenario_organisation.scenario_id$name
         Organisation............event_scenario_organisation.organisation_id$name
         Comments................event_scenario_organisation.comments

    *********************************************************************** -->
    
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="organisations" match="row" use="col[@field='Scenario']"/>
    <xsl:key name="scenarios" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Scenarios -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('scenarios', col[@field='Scenario'])[1])]">
                <xsl:call-template name="Scenario"/>
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Scenario Organisations -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="event_scenario_organisation">

            <!-- Link to Scenario -->
            <reference field="scenario_id" resource="event_scenario">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Scenario']"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']"/>
                </xsl:attribute>
            </reference>

            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrganisationName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrganisationName"/></data>
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
