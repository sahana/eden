<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Budget Staff Types - CSV Import Stylesheet

         CSV fields:
         Name...................budget_staff.name
         Grade..................budget_staff.grade
         Salary.................budget_staff.salary
         Currency...............budget_staff.currency # @todo
         Travel Cost............budget_staff.travel
         Comments...............budget_staff.comments

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
        <resource name="budget_staff">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="grade"><xsl:value-of select="col[@field='Grade']"/></data>
            <xsl:if test="col[@field='Salary']!=''">
                <data field="salary"><xsl:value-of select="col[@field='Salary']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Travel Cost']!=''">
                <data field="travel"><xsl:value-of select="col[@field='Travel Cost']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>
        </resource>
    </xsl:template>

</xsl:stylesheet>
