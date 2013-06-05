<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Resident Type - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Name...........................required.....name
         Comments.......................optional.....comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Create the Resident Type records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!--  Resident Type Record -->
    <xsl:template match="row">
        <resource name="stats_resident_type">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>
    </xsl:template>
</xsl:stylesheet>
