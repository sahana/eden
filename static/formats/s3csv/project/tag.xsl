<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Tags - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Name

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
        <resource name="project_tag">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
