<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Survey Template - CSV Import Stylesheet

         CSV fields:
         Name...................survey_template.name
         Description............survey_template.description
         Status.................survey_template.status
         Complete Question......survey_template.competion_qstn
         Date Question..........survey_template.date_qstn
         Time Question..........survey_template.time_qstn
         Location Question......survey_template.location_qstn
         Priority Question......survey_template.priority_qstn

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
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="status"><xsl:value-of select="col[@field='Status']"/></data>
            <data field="competion_qstn"><xsl:value-of select="col[@field='Complete Question']"/></data>
            <data field="date_qstn"><xsl:value-of select="col[@field='Date Question']"/></data>
            <data field="time_qstn"><xsl:value-of select="col[@field='Time Question']"/></data>
            <data field="location_detail"><xsl:value-of select="col[@field='Location Detail']"/></data>
            <data field="priority_qstn"><xsl:value-of select="col[@field='Priority Question']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
