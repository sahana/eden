<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Budget Locations - CSV Import Stylesheet

         CSV fields:

         Code...................budget_location.code
         Description............budget_location.description
         Subsistence Cost.......budget_location.subsistence
         Hazard Pay.............budget_location.hazard_pay
         Comments...............budget_location.comments

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
        <resource name="budget_location">
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <xsl:if test="col[@field='Description']!=''">
                <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Subsistence Cost']!=''">
                <data field="subsistence"><xsl:value-of select="col[@field='Subsistence Cost']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Hazard Pay']!=''">
                <data field="hazard_pay"><xsl:value-of select="col[@field='Hazard Pay']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>
        </resource>
    </xsl:template>

</xsl:stylesheet>
