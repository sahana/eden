<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:project="http://eden.sahanafoundation.org/project">

    <!-- **********************************************************************
         Project Organisations - CSV Import Stylesheet

         2011-12-16 / Dominic König <dominic[AT]aidiq[DOT]com>

         CSV column...........Format..........Content

         Project..............string..........Project Name
         Organisation.........string..........Organisation Name
         Role.................code............Organisation Role
         Funding Amount.......float...........Funding Amount
         Currency.............code............Currency of the Funding Amount

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- Project Organisation Roles, see models/09_project.py, project_organisation_types -->
    <project:organisation-role code="1">Host National Society</project:organisation-role>
    <project:organisation-role code="2">Partner National Society</project:organisation-role>
    <project:organisation-role code="3">Donor</project:organisation-role>

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

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="project_organisation">

            <!-- Organisation role, defaults to Partner NS -->
            <data field="role">
                <xsl:choose>
                    <xsl:when test="col[@field='Role']/text()">
                        <xsl:variable name="rolename" select="col[@field='Role']/text()"/>
                        <xsl:variable name="rolecode"
                                      select="document('')//project:organisation-role[text()=normalize-space($rolename)]/@code"/>
                        <xsl:if test="$rolecode"><xsl:value-of select="$rolecode"/></xsl:if>
                    </xsl:when>
                    <xsl:otherwise>2</xsl:otherwise>
                </xsl:choose>
            </data>

            <!-- Funding amount and currency -->
            <xsl:if test="col[@field='Amount']/text()">
                <data field="amount">
                    <xsl:value-of select="col[@field='Amount']"/>
                </data>
                <data field="currency">
                    <xsl:choose>
                        <xsl:when test="col[@field='Currency']/text()">
                            <xsl:value-of select="col[@field='Currency']/text()"/>
                        </xsl:when>
                        <xsl:otherwise>USD</xsl:otherwise>
                    </xsl:choose>
                </data>
            </xsl:if>

            <!-- Link to Project -->
            <reference field="project_id" resource="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Project:', $ProjectName)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Organisation:', $OrgName)"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Organisation:', $OrgName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>

        <resource name="project_project">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Project:', $ProjectName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ProjectName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
