<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GIS Projection - CSV Import Stylesheet

         CSV column...........Format..........Content

         UUID.................string..........Projection UUID
         Name.................string..........Projection Name
         EPSG.................integer.........Projection EPSG
         maxExtent............string..........Projection maxExtent
         maxResolution........float...........Projection maxResolution
         units................string..........Projection units

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
        <resource name="gis_projection">
            <xsl:attribute name="uuid">
                <xsl:value-of select="col[@field='UUID']"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="epsg"><xsl:value-of select="col[@field='EPSG']"/></data>
            <data field="maxExtent"><xsl:value-of select="col[@field='maxExtent']"/></data>
            <data field="maxResolution"><xsl:value-of select="col[@field='maxResolution']"/></data>
            <data field="units"><xsl:value-of select="col[@field='units']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
