<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Templates - CSV Import Stylesheet

         CSV fields:
         Name....................dc_template.name
         Master..................dc_template.master (defaults to dc_response)
         Layout..................dc_template.layout

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Templates -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Master">
            <xsl:value-of select="col[@field='Master']"/>
        </xsl:variable>

        <resource name="dc_template">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="layout"><xsl:value-of select="col[@field='Layout']"/></data>
            <xsl:if test="$Master!=''">
                <data field="master"><xsl:value-of select="$Master"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
