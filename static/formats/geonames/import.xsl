<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <xsl:output method="xml"/>

    <xsl:template match="locations">
        <s3xrc domain="geonames.org">
            <xsl:apply-templates select="./location"/>
        </s3xrc>
    </xsl:template>

    <xsl:template match="location">
        <xsl:variable name="uuid">
            <xsl:value-of select="./id/text()" />
        </xsl:variable>
        <xsl:if test="contains(./featureClass, 'ADM') or contains(./featureClass, 'PPL')">
            <resource name="gis_location">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="concat('www.geonames.org/', $uuid)" />
                </xsl:attribute>
                <xsl:variable name="level">
                    <xsl:choose>
                        <xsl:when test="./featureClass/text()='ADM1'">
                            <xsl:text>L1</xsl:text>
                        </xsl:when>
                        <xsl:when test="./featureClass/text()='ADM2'">
                            <xsl:text>L2</xsl:text>
                        </xsl:when>
                        <xsl:when test="./featureClass/text()='ADM3' or
                                        ./featureClass/text()='PPLC' or
                                        ./featureClass/text()='PPLA' or
                                        ./featureClass/text()='PPLA2' or
                                        ./featureClass/text()='PPLA3' or
                                        ./featureClass/text()='PPLA4'">
                            <xsl:text>L3</xsl:text>
                        </xsl:when>
                        <xsl:when test="./featureClass='ADM4' or contains(./featureClass, 'PPL')">
                            <xsl:text>L4</xsl:text>
                        </xsl:when>
                    </xsl:choose>
                </xsl:variable>
<!--                <xsl:attribute name="location">
                    <xsl:value-of select="./asciiName/text()"/>
                </xsl:attribute>
                <xsl:attribute name="level">
                    <xsl:value-of select="$level"/>
                </xsl:attribute>-->
                <data field="name">
                    <xsl:value-of select="./asciiName/text()"/>
                </data>
                <data field="feature_type" value="1"/>
                <data field="lat">
                    <xsl:value-of select="./lat/text()"/>
                </data>
                <data field="lon">
                    <xsl:value-of select="./lon/text()"/>
                </data>
                <data field="level">
                    <xsl:value-of select="$level"/>
                </data>
            </resource>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
