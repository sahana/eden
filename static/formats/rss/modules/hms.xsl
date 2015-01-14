<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- HMS -->

    <!-- hms_hospital -->
    <xsl:template match="resource[@name='hms_hospital']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='name']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='city']/text()"/>
            <xsl:if test="./reference[@field='location_id']/text()">
                <xsl:value-of select="concat(' [', ./reference[@field='location_id']/text(), ']')"/>
            </xsl:if>
            &lt;br/&gt;&lt;br/&gt;
            <xsl:text>Facility Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./resource[@name='hms_status']/data[@field='facility_status']/text()">
                    <xsl:value-of select="./resource[@name='hms_status']/data[@field='facility_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Clinical Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./resource[@name='hms_status']/data[@field='clinical_status']/text()">
                    <xsl:value-of select="./resource[@name='hms_status']/data[@field='clinical_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Morgue Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./resource[@name='hms_status']/data[@field='morgue_status']/text()">
                    <xsl:value-of select="./resource[@name='hms_status']/data[@field='morgue_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Security Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./resource[@name='hms_status']/data[@field='security_status']/text()">
                    <xsl:value-of select="./resource[@name='hms_status']/data[@field='security_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Beds Available: </xsl:text>
            <xsl:choose>
                <xsl:when test="./data[@field='available_beds']/text()">
                    <xsl:value-of select="./data[@field='available_beds']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
        </description>
    </xsl:template>

    <!-- hms_hrequest -->
    <xsl:template match="resource[@name='hms_hrequest']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='subject']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='message']/text()"/>
        </description>
    </xsl:template>

</xsl:stylesheet>
