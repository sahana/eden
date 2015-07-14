<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Programmes - CSV Import Stylesheet

         CSV column...........Format..........Content

         Organisation.........string..........Organisation
         Name.................string..........Name
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:key name="orgs" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:call-template name="Programme" />
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
    <xsl:template name="Programme">

        <xsl:param name="Field">Name</xsl:param>

        <xsl:variable name="Name" select="col[@field=$Field]/text()"/>
        <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
        <resource name="project_programme">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('PRG:', $Name)"/>
            </xsl:attribute>
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Organisation:', col[@field='Organisation']/text())"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="$Name"/></data>
            <xsl:if test="$Field='Name' and $Comments!=''">
                <data field="comments"><xsl:value-of select="$Comments"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ProgrammeLink">

        <xsl:param name="Field">Programme</xsl:param>

        <xsl:variable name="Name" select="col[@field=$Field]/text()"/>
        <xsl:if test="$Name!=''">
            <resource name="project_programme_project">
                <reference field="programme_id" resource="project_programme">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('PRG:', $Name)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
