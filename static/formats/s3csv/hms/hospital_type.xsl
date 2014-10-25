<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Hospital Facility Types - CSV Import Stylesheet

         CSV column...........Format..........Content

         Type.................string..........Hospital Facility Type Name
         UUID (optional)......string..........hms_hospital_type.uuid
         Comments (optional)..string..........Comments

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
        <resource name="hms_hospital_type">
            <xsl:if test="col[@field='UUID']!=''">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="col[@field='UUID']"/>
                </xsl:attribute>
            </xsl:if>
            <data field="name"><xsl:value-of select="col[@field='Type']"/></data>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>