<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- CAP -->

    <!-- cap_info -->
    <xsl:template match="resource[@name='cap_info']" mode="contents">
        <xsl:if test="./data[@field='is_template' and @value='false']">
            <title>
                <xsl:value-of select="./data[@field='headline']/text()"/>
            </title>
            <description>
                <xsl:value-of select="./data[@field='description']/text()"/>
            </description>
            <link>
                <!--info-id substring after last character "/" --> 
                <xsl:variable name="info-id">
                    <xsl:call-template name="substring-after-last">
                        <xsl:with-param name="string" select="./@url" />
                        <xsl:with-param name="delimiter" select="'/'" />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="alert-uuid" select="reference[@resource='cap_alert']/@uuid"/>
                <xsl:variable name="alert-url" select="following-sibling::resource[@name='cap_alert' and @uuid=$alert-uuid]/@url"/>
                <xsl:value-of select="concat($alert-url,'/info/',$info-id,'.cap')"/>
            </link>
            <pubDate>
                <xsl:variable name="alert-uuid" select="reference[@resource='cap_alert']/@uuid"/>
                <xsl:value-of select="following-sibling::resource[@name='cap_alert' and @uuid=$alert-uuid]/data[@field='sent']/text()"/>
            </pubDate>
            <category>
                <xsl:value-of select="./data[@field='category']/text()"/>
            </category>
            <author>
                <xsl:value-of select="./data[@field='sender_name']/text()"/>
            </author>
        </xsl:if>
    </xsl:template>

    <xsl:template name="substring-after-last">
        <xsl:param name="string"/>
        <xsl:param name="delimiter"/>
        <xsl:choose>
            <xsl:when test="contains($string, $delimiter)">
                <xsl:call-template name="substring-after-last">
                    <xsl:with-param name="string"
                        select="substring-after($string, $delimiter)"/>
                    <xsl:with-param name="delimiter" select="$delimiter"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of
                    select="$string"/>
                </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
