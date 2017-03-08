<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Gardens (Rural Agriculture) - CSV Import Stylesheet
         
         CSV column...........Format..........Content

         Code.................string..........Name
         Comments.............string..........Comments
         WKT..................string..........Polygon

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
        <resource name="stdm_garden">
            <data field="name"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Link to Location -->
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <data field="name"><xsl:value-of select="col[@field='Code']"/></data>
                    <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                </resource>
            </reference>
            
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
