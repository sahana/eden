<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Feature Classes - CSV Import Stylesheet

         CSV column...........Format..........Content

         UUID.................string..........Class UUID
         Name.................string..........Class Name
         Marker...............string..........Class Marker Name
         GPS Marker...........string..........Class GPS Marker
         Resource.............string..........Class Resource
         Filter Field.........string..........Class Filter Field
         Filter Value.........string..........Class Filter Value

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="markers" match="row" use="col[@field='Marker']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Markers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('markers',
                                                                   col[@field='Marker'])[1])]">
                <xsl:call-template name="Marker"/>
            </xsl:for-each>

            <!-- Feature Classes -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>

        <resource name="gis_feature_class">
            <xsl:attribute name="uuid">
                <xsl:value-of select="col[@field='UUID']"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:if test="col[@field='GPS Marker']">
                <data field="gps_marker"><xsl:value-of select="col[@field='GPS Marker']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Resource']">
                <data field="resource"><xsl:value-of select="col[@field='Resource']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Filter Field']">
                <data field="filter_field"><xsl:value-of select="col[@field='Filter Field']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Filter Value']">
                <data field="filter_value"><xsl:value-of select="col[@field='Filter Value']"/></data>
            </xsl:if>
            <xsl:if test="$Marker">
                <reference field="marker_id" resource="gis_marker">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Marker"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Marker">

        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>
    
        <xsl:if test="$Marker">
            <resource name="gis_marker">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Marker"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Marker"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
