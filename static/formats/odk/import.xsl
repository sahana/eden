<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <xsl:output method="xml"/>

    <xsl:variable name="outermostElementName" select="name(/*)" />

    <xsl:template match="/*">
        <s3xml>
            <resource name="{$outermostElementName}">
                <xsl:for-each select="child::*">
                    <xsl:variable name="ChildName" select="name(.)" />
                    <xsl:choose>
                        <xsl:when test="$ChildName='pe_id'">
                            <reference field="{$ChildName}" resource="pr_pentity">
                                <xsl:attribute name="uuid">
                                    <xsl:value-of select="."/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                        <xsl:otherwise>
                            <data field="{$ChildName}">
                                <xsl:value-of select="."/>
                            </data>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </resource>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
