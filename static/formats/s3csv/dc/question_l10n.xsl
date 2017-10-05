<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Questions - CSV Import Stylesheet

         CSV fields:
         Language....................dc_question_l10n.language (2 letter ISO code)
         Template....................dc_template.name
         Question....................dc_question.name
         Translation.................dc_question_l10n.name_l10n
         Options.....................dc_question_l10n.options_l10n
         Tooltip.....................dc_question_l10n.tooltip_l10n

         @ToDo: Support templates with the same Question Name in multiple places

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="template" match="row" use="col[@field='Template']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Templates -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('template',
                                                                       col[@field='Template'])[1])]">
                <xsl:call-template name="Template"/>
            </xsl:for-each>

            <!-- Question Translations -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="question" select="col[@field='Question']/text()"/>

        <resource name="dc_question">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$question"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$question"/></data>
            <!-- Link to Template -->
            <reference field="template_id" resource="dc_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>
        </resource>

        <resource name="dc_question_l10n">
            <data field="language"><xsl:value-of select="col[@field='Language']"/></data>
            <data field="name_l10n"><xsl:value-of select="col[@field='Translation']"/></data>
            <data field="options_l10n"><xsl:value-of select="col[@field='Options']"/></data>
            <data field="tooltip_l10n"><xsl:value-of select="col[@field='Tooltip']"/></data>

            <reference field="question_id" resource="dc_question">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$question"/>
                </xsl:attribute>
            </reference>
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

</xsl:stylesheet>
