<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Scenarios - CSV Import Stylesheet

         CSV fields:
         Scenario................event_scenario.name
         Incident Type...........event_scenario.incident_type_id$name
         Comments................event_scenario.comments

    *********************************************************************** -->
    
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="incident_types" match="row" use="col[@field='Incident Type']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Incident Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('incident_types', col[@field='Incident Type'])[1])]">
                <xsl:call-template name="IncidentType"/>
            </xsl:for-each>

            <!-- Scenarios -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="ScenarioName" select="col[@field='Scenario']/text()"/>

        <resource name="event_scenario">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ScenarioName"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$ScenarioName"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Link to Incident Type -->
            <reference field="incident_type_id" resource="event_incident_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Incident Type']"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="IncidentType">

        <xsl:variable name="IncidentType" select="col[@field='Incident Type']/text()"/>

        <resource name="event_incident_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$IncidentType"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$IncidentType"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
