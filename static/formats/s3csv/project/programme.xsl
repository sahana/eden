<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Programmes - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Name
         Comments.............string..........Comments

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
        <xsl:call-template name="Programme" />
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
