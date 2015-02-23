<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- DVI -->

    <!-- dvi_recreq -->
    <xsl:template match="resource[@name='dvi_recreq']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='marker']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='date']/text()"/>
        </description>
    </xsl:template>

</xsl:stylesheet>
