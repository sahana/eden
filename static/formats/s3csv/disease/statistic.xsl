<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Disease Statistics - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Name
         Description..........string..........Description

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
        <xsl:variable name="description" select="col[@field='Description']"/>

        <resource name="stats_demographic">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:if test="$description!=''">
                <data field="description"><xsl:value-of select="$description"/></data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
