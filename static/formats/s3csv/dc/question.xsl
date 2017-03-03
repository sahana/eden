<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Questions - CSV Import Stylesheet

         CSV fields:
         Template....................dc_template.name
         Question....................dc_question.name
         Type........................dc_question.field_type
         Options.....................dc_question.options
         Required....................dc_question.require_not_empty
         Tooltip.....................dc_question.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="template" match="row" use="col[@field='Template']"/>
    <xsl:key name="section" match="row" use="col[@field='Section']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Templates -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('template',
                                                                       col[@field='Template'])[1])]">
                <xsl:call-template name="Template"/>
            </xsl:for-each>

            <!-- Sections -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('section',
                                                                       col[@field='Section'])[1])]">
                <xsl:call-template name="Section"/>
            </xsl:for-each>

            <!-- Questions -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="dc_question">
            <data field="name"><xsl:value-of select="col[@field='Question']"/></data>
            <data field="options"><xsl:value-of select="col[@field='Options']"/></data>
            <data field="require_not_empty"><xsl:value-of select="col[@field='Required']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Tooltip']"/></data>

            <!-- Link to Template -->
            <reference field="template_id" resource="dc_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Section -->
            <reference field="section_id" resource="dc_section">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Section']"/>
                </xsl:attribute>
            </reference>

            <!-- Field Type -->
            <xsl:variable name="Type">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="col[@field='Type']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="$Type='TEXT' or $Type='STRING'">
                    <data field="field_type">1</data>
                </xsl:when>
                <xsl:when test="$Type='NUMBER' or $Type='INTEGER'">
                    <data field="field_type">2</data>
                </xsl:when>
                <xsl:when test="$Type='FRACTION' or $Type='FLOAT'">
                    <data field="field_type">3</data>
                </xsl:when>
                <xsl:when test="$Type='YES/NO' or $Type='Y/N' or $Type='BOOLEAN'">
                    <data field="field_type">4</data>
                </xsl:when>
                <xsl:when test="$Type='YES/NO/DONT KNOW' or $Type='Y/N/DK'">
                    <data field="field_type">5</data>
                </xsl:when>
                <xsl:when test="$Type='OPTIONS' or $Type='SELECT'">
                    <data field="field_type">6</data>
                </xsl:when>
                <xsl:when test="$Type='DATE'">
                    <data field="field_type">7</data>
                </xsl:when>
                <xsl:when test="$Type='DATETIME'">
                    <data field="field_type">8</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Default to String -->
                    <data field="field_type">1</data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Required -->
            <xsl:variable name="Required">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="col[@field='Required']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="starts-with($Required, 'Y') or starts-with($Required, 'T')">
                    <data field="require_not_empty" value="true">True</data>
                </xsl:when>
                <xsl:when test="starts-with($Required, 'N') or starts-with($Required, 'F')">
                    <data field="require_not_empty" value="false">False</data>
                </xsl:when>
            </xsl:choose>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Template">
        <xsl:variable name="template" select="col[@field='Template']/text()"/>

        <resource name="dc_template">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$template"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$template"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Section">
        <xsl:variable name="section" select="col[@field='Section']/text()"/>

        <resource name="dc_section">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$section"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$section"/></data>

            <!-- Link to Template -->
            <reference field="template_id" resource="dc_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
