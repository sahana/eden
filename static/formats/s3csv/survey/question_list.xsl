<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey-Template - CSV Import Stylesheet

         CSV fields:
         Template..............survey_template.name
         Template Description..survey_template.description
         Complete Question......survey_template.competion_qstn
         Date Question..........survey_template.date_qstn
         Time Question..........survey_template.time_qstn
         Location Question......survey_template.location_qstn
         Priority Question......survey_template.priority_qstn
         Section...............survey_section.name
         Section Description...survey_section.description
         Section Position......survey_section.posn
         Question..............survey_question.name
         Question Type.........survey_question.type
         Question Notes........survey_question.notes
         Question Code.........survey_question.code
         Question Position.....survey_question_list.posn
         metaD1................survey_question_metadata.descriptor
         metaV1................survey_question_metadata.value
         metaD2................survey_question_metadata.descriptor
         metaV2................survey_question_metadata.value
         metaD3................survey_question_metadata.descriptor
         metaV3................survey_question_metadata.value


    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:key name="survey_template"
             match="row"
             use="col[@field='Template']"/>
    <xsl:key name="survey_section"
             match="row"
             use="col[@field='Section']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('survey_template',
                                                        col[@field='Template'])[1])]">
                <xsl:call-template name="Template"/>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('survey_section',
                                                        col[@field='Section'])[1])]">
                <xsl:call-template name="Section"/>
            </xsl:for-each>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="survey_question">
            <xsl:attribute name="tuid">
                <xsl:value-of select="col[@field='Question Code']"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Question']"/></data>
            <data field="type"><xsl:value-of select="col[@field='Question Type']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Question Code']"/></data>
            <data field="notes"><xsl:value-of select="col[@field='Question Notes']"/></data>
            <data field="metadata"><xsl:value-of select="col[@field='Meta Data']"/></data>
        </resource>

        <resource name="survey_question_list">
            <data field="posn"><xsl:value-of select="col[@field='Question Position']"/></data>
            <data field="notes"><xsl:value-of select="col[@field='Question Notes']"/></data>
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
            <!-- Link to Questions -->
            <reference field="question_id" resource="survey_question">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Question Code']"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>
    <!-- ****************************************************************** -->
    <xsl:template name="Template">
        <xsl:variable name="template" select="col[@field='Template']/text()"/>

        <!-- Create the survey template -->
        <resource name="survey_template">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$template"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$template"/></data>
            <data field="description"><xsl:value-of select="col[@field='Template Description']"/></data>
            <data field="competion_qstn"><xsl:value-of select="col[@field='Complete Question']"/></data>
            <data field="date_qstn"><xsl:value-of select="col[@field='Date Question']"/></data>
            <data field="time_qstn"><xsl:value-of select="col[@field='Time Question']"/></data>
            <data field="location_detail"><xsl:value-of select="col[@field='Location Detail']"/></data>
            <data field="priority_qstn"><xsl:value-of select="col[@field='Priority Question']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Section">
        <xsl:variable name="section" select="col[@field='Section']/text()"/>

        <!-- Create the survey section -->
        <resource name="survey_section">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$section"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$section"/></data>
            <data field="description"><xsl:value-of select="col[@field='Section Description']"/></data>
            <data field="posn"><xsl:value-of select="col[@field='Section Position']"/></data>
            <!-- Link to Template -->
            <reference field="template_id" resource="survey_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
