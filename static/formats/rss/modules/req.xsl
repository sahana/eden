<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- Req -->
    
    <!-- req_need -->
    <xsl:template match="resource[@name='req_need']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='name']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='description']/text()"/>
            <xsl:value-of select="$newline"/>
            <xsl:value-of select="./data[@field='status']/text()"/>
            <xsl:value-of select="$newline"/>
            <xsl:value-of select="./data[@field='comments']/text()"/>
        </description>
    </xsl:template>

</xsl:stylesheet>
