<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Sectors and Subsectors - CSV Import Stylesheet

         CSV Column              Type          Description
         Abrv....................string........Abbreviation (unique)
         Name....................string........Name (defaults to Abbreviation)
         SubsectorOf.............string........Abbreviation of the
                                                    Sectorname (for subsectors)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row[normalize-space(col[@field='SubsectorOf'])='']"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:call-template name="Sector"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Sector">
        <xsl:variable name="SectorName" select="normalize-space(col[@field='Name']/text())"/>
        <xsl:variable name="SectorAbrv" select="normalize-space(col[@field='Abrv']/text())"/>
        <xsl:variable name="SubsectorOf" select="normalize-space(col[@field='SubsectorOf']/text())"/>

        <xsl:variable name="resource">
            <xsl:choose>
                <xsl:when test="$SubsectorOf=''">org_sector</xsl:when>
                <xsl:otherwise>org_subsector</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <resource>
            <xsl:attribute name="name">
                <xsl:value-of select="$resource"/>
            </xsl:attribute>
            <data field="abrv"><xsl:value-of select="$SectorAbrv"/></data>
            <data field="name">
                <xsl:choose>
                    <xsl:when test="$SectorName!=''">
                        <xsl:value-of select="$SectorName"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$SectorAbrv"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>
            <xsl:if test="$resource='org_sector'">
                <xsl:for-each select="//row[normalize-space(col[@field='SubsectorOf'])=$SectorAbrv]">
                    <xsl:call-template name="Sector"/>
                </xsl:for-each>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
