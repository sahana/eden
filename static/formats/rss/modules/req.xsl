<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- Req -->
    
    <!-- req_req -->
    <xsl:template match="resource[@name='req_req']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='req_ref']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./reference[@field='site_id']/text()"/>
            <xsl:value-of select="$newline"/>
            <xsl:value-of select="./data[@field='priority']/text()"/>
            <xsl:value-of select="$newline"/>
            <xsl:value-of select="./data[@field='purpose']/text()"/>
            <xsl:value-of select="$newline"/>
            <xsl:value-of select="./data[@field='comments']/text()"/>
        </description>
    </xsl:template>

</xsl:stylesheet>
