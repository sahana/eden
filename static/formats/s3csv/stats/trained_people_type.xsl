<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Trained People Type - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Name...........................required.....name

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Create the Stats Group Type records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!--  Trained People Type Record -->
    <xsl:template match="row">
        <resource name="stats_trained_people_type">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
        </resource>
    </xsl:template>
</xsl:stylesheet>
