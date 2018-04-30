<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Hazards - CSV Import Stylesheet

         CSV column...........Format..........Content

         Start Date...........date............project_window.start_date
         End Date.............date............project_window.end_date

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
        <resource name="project_window">
            <data field="start_date"><xsl:value-of select="col[@field='Start Date']"/></data>
            <data field="end_date"><xsl:value-of select="col[@field='End Date']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
