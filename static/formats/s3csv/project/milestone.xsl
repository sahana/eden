<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Milestones - CSV Import Stylesheet

         CSV column...........Format..........Content

         Organisation.........string..........Project Organisation
         Project..............string..........Project Name
         Milestone............string..........Milestone name
         Date.................date............Milestone date
         Comments.............string..........Milestone comments

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="projects" match="row" use="col[@field='Project']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations',
                                                                   col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projects',
                                                                   col[@field='Project'])[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <!-- Milestones -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="project_milestone">
            <data field="name"><xsl:value-of select="col[@field='Milestone']"/></data>
            <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            <!-- Link to Project -->
            <reference field="project_id" resource="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Project']"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$OrganisationName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrganisationName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrganisationName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>

        <xsl:if test="$ProjectName!=''">
            <resource name="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ProjectName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ProjectName"/></data>
                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Organisation']"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
