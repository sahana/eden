<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Scenario Human Resources - CSV Import Stylesheet

         CSV fields:
         Scenario................event_scenario_human_resource.scenario_id$name
         Job Title...............event_scenario_human_resource.job_title_id$name
         Comments................event_scenario_human_resource.comments

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

            <!-- Scenario Tasks -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="ScenarioName" select="col[@field='Scenario']/text()"/>

        <resource name="event_scenario_human_resource">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ScenarioName"/>
            </xsl:attribute>

            <!-- Link to Scenario -->
            <reference field="scenario_id" resource="event_scenario">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Scenario']"/>
                </xsl:attribute>
            </reference>

            <!-- Job Title -->
            <reference field="job_title_id" resource="hrm_job_title">
                <resource name="hrm_job_title">
                    <data field="name"><xsl:value-of select="col[@field='Job Title']"/></data>
                    <data field="type">4</data>
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
