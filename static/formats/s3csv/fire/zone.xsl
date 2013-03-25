<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Fire Zone - CSV Import Stylesheet
         
         CSV column...........Format..........Content

         Name.................string..........Name
         Type.................string..........Zone Type
         Comments.............string..........Comments
         WKT..................string..........Polygon

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="type" match="row" use="col[@field='Type']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type',
                                                                       col[@field='Type'])[1])]">
                <xsl:call-template name="Type"/>
            </xsl:for-each>

            <!-- Process all table rows for Zone records -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="fire_zone">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Link to Zone Type -->
            <reference field="zone_type_id" resource="fire_zone_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Type']"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Location -->
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
                    <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                </resource>
            </reference>
            
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Type">
        <xsl:variable name="type" select="col[@field='Type']/text()"/>

        <resource name="fire_zone_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$type"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$type"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
