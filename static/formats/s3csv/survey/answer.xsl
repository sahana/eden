<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Survey Answer - CSV Import Stylesheet

         - this is used in the survey model, by the function importAnswers
           which is why it uses the id's directly

         CSV fields:
         complete_id.......survey_answer.complete_id
         question_code.....survey_answer.question_id
         value.............survey_answer.value

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

        <resource name="survey_question">
            <xsl:attribute name="tuid">
                <xsl:value-of select="col[@field='question_code']"/>
            </xsl:attribute>
            <data field="code"><xsl:value-of select="col[@field='question_code']"/></data>
        </resource>

        <!-- Lookup table survey_template -->
        <resource name="survey_answer">
            <data field="value"><xsl:value-of select="col[@field='value']"/></data>
            <data field="complete_id"><xsl:value-of select="col[@field='complete_id']"/></data>
            <!-- Link to Template -->
            <reference field="question_id" resource="survey_question">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='question_code']"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
