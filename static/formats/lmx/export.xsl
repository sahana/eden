<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:lm="http://www.nokia.com/schemas/location/landmarks/1/0">

    <!-- Sahana Eden XSLT Export Template

        Transformation of
            Sahana Eden GIS Location
        into
            NOKIA Landmark Location
    -->

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <lm:lmx>
            <lm:landmarkCollection>
                <xsl:apply-templates select="./s3xml"/>
            </lm:landmarkCollection>
        </lm:lmx>
    </xsl:template>

    <xsl:template match="s3xml">
        <lm:name>
            <xsl:choose>
                <xsl:when test="./@domain">
                    <xsl:value-of select="concat('Sahana Eden GIS Locations / ', ./@domain)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>Sahana Eden GIS Locations</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </lm:name>
        <xsl:apply-templates select="./resource[@name='gis_location']"/>
    </xsl:template>

    <xsl:template match="resource[@name='gis_location']">
        <xsl:if test="./data[@field='name'] and ./data[@field='lat'] and ./data[@field='lon']">
            <lm:landmark>
                <lm:name>
                    <xsl:value-of select="./data[@field='name']"/>
                </lm:name>
                <lm:coordinates>
                    <lm:latitude>
                        <xsl:value-of select="./data[@field='lat']"/>
                    </lm:latitude>
                    <lm:longitude>
                        <xsl:value-of select="./data[@field='lon']"/>
                    </lm:longitude>
                </lm:coordinates>
            </lm:landmark>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
