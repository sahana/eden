<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Budgets - CSV Import Stylesheet

         CSV fields:
         Name...................budget_budget.name
         Description............budget_budget.description
         Staff..................[Code:Location:Quantity:Months,...] @ToDO
         Bundles................[Code:Location:Quantity:Months,...] @ToDO
         Comments...............budget_budget.comments

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
        <resource name="budget_budget">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:if test="col[@field='Description']!=''">
                <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Total Volume']!=''">
                <data field="total_volume"><xsl:value-of select="col[@field='Total Volume']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
