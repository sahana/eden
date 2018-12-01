<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Response Status - CSV Import Stylesheet

         CSV column...........Format..........Content

         Position.............integer.........Workflow Position
         Status...............string..........Status Name
         Default..............string..........is default status
                                              true|false
         Closed...............string..........cases with this status are closed
                                              true|false
         Color................string..........color code (rrggbb)
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="dvr_response_status">

            <data field="workflow_position">
                <xsl:value-of select="col[@field='Position']/text()"/>
            </data>

            <data field="name">
                <xsl:value-of select="col[@field='Status']/text()"/>
            </data>

            <xsl:call-template name="Boolean">
                <xsl:with-param name="column">Default</xsl:with-param>
                <xsl:with-param name="field">is_default</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="Boolean">
                <xsl:with-param name="column">Closed</xsl:with-param>
                <xsl:with-param name="field">is_closed</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="Boolean">
                <xsl:with-param name="column">Default Closure</xsl:with-param>
                <xsl:with-param name="field">is_default_closure</xsl:with-param>
            </xsl:call-template>

            <data field="color">
                <xsl:value-of select="col[@field='Color']/text()"/>
            </data>

            <data field="comments">
                <xsl:value-of select="col[@field='Comments']/text()"/>
            </data>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Helper for boolean fields -->
    <xsl:template name="Boolean">

        <xsl:param name="column"/>
        <xsl:param name="field"/>

        <data>
            <xsl:attribute name="field">
                <xsl:value-of select="$field"/>
            </xsl:attribute>
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="col[@field=$column]/text()='true'">
                        <xsl:value-of select="'true'"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'false'"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
