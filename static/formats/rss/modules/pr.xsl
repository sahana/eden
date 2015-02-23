<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- PR -->

    <!-- pr_person -->
    <xsl:template match="resource[@name='pr_person']" mode="contents">
        <xsl:variable name="first_name" select="./data[@field='first_name']/text()"/>
        <xsl:variable name="middle_name" select="./data[@field='middle_name']/text()"/>
        <xsl:variable name="last_name" select="./data[@field='last_name']/text()"/>
        <title>
            <xsl:choose>
                <xsl:when test="$middle_name and $last_name">
                    <xsl:value-of select="concat($first_name, ' ', $middle_name, ' ', $last_name)"/>
                </xsl:when>
                <xsl:when test="$last_name">
                    <xsl:value-of select="concat($first_name, ' ', $last_name)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$first_name"/>
                </xsl:otherwise>
            </xsl:choose>
        </title>
        <description>
            <xsl:if test="./data[@field='pr_pe_label']/text()">
                <xsl:text>ID Label:</xsl:text>
                <xsl:value-of select="./data[@field='pr_pe_label']/text()"/>
            </xsl:if>
        </description>
    </xsl:template>

    <!-- pr_presence -->
    <xsl:template match="resource[@name='pr_presence']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='datetime']/text()"/>
        </title>
        <description>
            &lt;b&gt;
            <xsl:value-of select="./data[@field='presence_condition']/text()"/>
            &lt;/b&gt;
            <xsl:text>: </xsl:text>
            <xsl:value-of select="./data[@field='location_details']/text()"/>
            <xsl:if test="./reference[@field='location_id']/text()">
                <xsl:value-of select="concat(' [',./reference[@field='location_id']/text(),']')"/>
            </xsl:if>
            <xsl:if test="./data[@field='proc_desc']/text()">
                &lt;br/&gt;
                <xsl:value-of select="./data[@field='proc_desc']/text()"/>
            </xsl:if>
        </description>
    </xsl:template>

</xsl:stylesheet>
