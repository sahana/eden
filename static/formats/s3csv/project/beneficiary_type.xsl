<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Beneficiary Types - CSV Import Stylesheet

         2011-12-16 / Dominic König <dominic[AT]aidiq[DOT]com>

         CSV column...........Format..........Content

         Name.................string..........Type Name

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
        <resource name="project_beneficiary_type">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
