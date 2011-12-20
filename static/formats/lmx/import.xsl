<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:lm="http://www.nokia.com/schemas/location/landmarks/1/0">

    <!-- Sahana Eden XSLT Import Template

        Transformation of
            NOKIA Landmark Location
        into
            Sahana Eden GIS Location
    -->

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select=".//lm:landmark"/>
        </s3xml>
    </xsl:template>

    <xsl:template match="lm:landmark">
        <resource name="gis_location">
            <data field="gis_feature_type" value="1">Point</data>
            <xsl:apply-templates select="./lm:name"/>
            <xsl:apply-templates select="./lm:coordinates"/>
        </resource>
    </xsl:template>

    <xsl:template match="lm:name">
        <data field="name">
            <xsl:value-of select="./text()"/>
        </data>
    </xsl:template>

    <xsl:template match="lm:coordinates">
        <data field="lat">
            <xsl:value-of select="./lm:latitude/text()"/>
        </data>
        <data field="lon">
            <xsl:value-of select="./lm:longitude/text()"/>
        </data>
    </xsl:template>

</xsl:stylesheet>
