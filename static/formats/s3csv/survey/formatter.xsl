<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey_formatter - CSV Import Stylesheet

         - use for import to survey/formatter resource

         CSV fields:
         Template..............survey_template.name
         Section...............survey_section.name
         Posn..................survey_section.posn
         Method................survey_formatter.method
         Rules.................survey_formatter.rules


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

        <!-- Create the survey template -->
        <resource name="survey_template">
            <xsl:attribute name="tuid">
                <xsl:value-of select="col[@field='Template']"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Template']"/></data>
        </resource>

        <resource name="survey_section">
            <xsl:attribute name="tuid">
                <xsl:value-of select="col[@field='Section']"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Section']"/></data>
            <data field="posn"><xsl:value-of select="col[@field='Posn']"/></data>
            <!-- Link to Template -->
            <reference field="template_id" resource="survey_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>
        </resource>

        <resource name="survey_formatter">
            <data field="method"><xsl:value-of select="col[@field='Method']"/></data>
            <data field="rules"><xsl:value-of select="col[@field='Rules']"/></data>
            <!-- Link to Template -->
            <reference field="template_id" resource="survey_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Sections -->
            <reference field="section_id" resource="survey_section">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Section']"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
