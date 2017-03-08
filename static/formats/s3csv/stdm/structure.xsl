<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Structures (Informal Settlements) - CSV Import Stylesheet
         
         CSV column...........Format..........Content

         Name.................string..........Name2
         Code.................string..........Name
         Ownership Type.......string..........Ownership Type
         Recognition Status...boolean.........Recognition Status
         Comments.............string..........Comments
         WKT..................string..........Polygon

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="ownership_type" match="row" use="col[@field='Ownership Type']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Ownership Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('ownership_type',
                                                                       col[@field='Ownership Type'])[1])]">
                <xsl:call-template name="OwnershipType"/>
            </xsl:for-each>

            <!-- Process all table rows for Structure records -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="stdm_structure">
            <data field="name2"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="name"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Recognition Status -->
            <xsl:variable name="RecognitionStatus">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="col[@field='Recognition Status']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="starts-with($RecognitionStatus, 'Y') or starts-with($RecognitionStatus, 'T')">
                    <data field="recognition_status" value="true">True</data>
                </xsl:when>
                <xsl:when test="starts-with($RecognitionStatus, 'N') or starts-with($RecognitionStatus, 'F')">
                    <data field="recognition_status" value="false">False</data>
                </xsl:when>
            </xsl:choose>

            <!-- Link to Ownership Type -->
            <reference field="ownership_type_id" resource="stdm_ownership_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Ownership Type']"/>
                </xsl:attribute>
            </reference>

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
    <xsl:template name="OwnershipType">
        <xsl:variable name="type" select="col[@field='Ownership Type']/text()"/>

        <resource name="stdm_ownership_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$type"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$type"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
