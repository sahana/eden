<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#">

    <!-- ****************************************************************** -->
    <!-- CMS -->

    <!-- cms_post -->
    <xsl:template match="resource[@name='cms_post']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='title']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='body']/text()"/>
        </description>
        <!-- Author -->
        <xsl:if test="./reference[@field='person_id']">
            <dc:author>
                <xsl:value-of select="./reference[@field='person_id']/text()"/>
            </dc:author>
        </xsl:if>
        <!-- Location -->
        <xsl:if test="./reference[@field='location_id']">
            <geo:lat>
                <xsl:value-of select="./reference[@field='location_id']/@lat"/>
            </geo:lat>
            <geo:long>
                <xsl:value-of select="./reference[@field='location_id']/@lon"/>
            </geo:long>
        </xsl:if>
        <!-- Tags -->
        <xsl:for-each select="./resource[@name='cms_tag_post']">
            <xsl:variable name="uuid" select="reference[@field='tag_id']/@uuid"/>
            <xsl:variable name="category" select="//resource[@uuid=$uuid]/data[@field='name']/text()"/>
            <category>
                <xsl:value-of select="$category"/>
            </category>
        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>
