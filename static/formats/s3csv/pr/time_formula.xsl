<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Availability Slots: Time Formulae - CSV Import Stylesheet

         CSV fields:
         Name............................pr_time_formula.name
         All Day.........................pr_time_formula.all_day
         Start...........................pr_time_formula.start_time
         End.............................pr_time_formula.end_time

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="AllDay">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='All Day']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="pr_time_formula">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:choose>
                <xsl:when test="$AllDay='Y'">
                    <data field="all_day" value="true">True</data>
                </xsl:when>
                <xsl:when test="$AllDay='YES'">
                    <data field="all_day" value="true">True</data>
                </xsl:when>
                <xsl:when test="$AllDay='T'">
                    <data field="all_day" value="true">True</data>
                </xsl:when>
                <xsl:when test="$AllDay='TRUE'">
                    <data field="all_day" value="true">True</data>
                </xsl:when>
                <xsl:when test="$AllDay='N'">
                    <data field="all_day" value="false">False</data>
                </xsl:when>
                <xsl:when test="$AllDay='NO'">
                    <data field="all_day" value="false">False</data>
                </xsl:when>
                <xsl:when test="$AllDay='F'">
                    <data field="all_day" value="false">False</data>
                </xsl:when>
                <xsl:when test="$AllDay='FALSE'">
                    <data field="all_day" value="false">False</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Use System Default -->
                </xsl:otherwise>
            </xsl:choose>
            <data field="start_time"><xsl:value-of select="col[@field='Start']"/></data>
            <data field="end_time"><xsl:value-of select="col[@field='End']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
