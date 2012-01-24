<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Markers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Marker Name
         Height...............integer.........Marker Height
         Width................integer.........Marker Width
         Image................string..........Marker Image

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="gis_marker">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="height"><xsl:value-of select="col[@field='Height']"/></data>
            <data field="width"><xsl:value-of select="col[@field='Width']"/></data>
            <data field="image">
                <xsl:attribute name="filename">
                    <xsl:value-of select="col[@field='Image']"/>
                </xsl:attribute>
                <xsl:attribute name="url">
                    <xsl:text>local</xsl:text>
                </xsl:attribute>
            </data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
