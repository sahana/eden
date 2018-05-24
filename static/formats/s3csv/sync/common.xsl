<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Common Templates for Sync-related imports -->

    <xsl:output method="xml"/>

    <!-- Template for repository references (column "Repository") -->
    <xsl:template name="Repository">

        <xsl:variable name="Name" select="col[@field='Repository']/text()"/>
        <xsl:if test="$Name!=''">
            <resource name="sync_repository">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('REPOSITORY:', $Name)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>
