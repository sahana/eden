<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Parcels (Local Government) - CSV Import Stylesheet
         
         CSV column...........Format..........Content

         Code.................string..........Name
         Area.................string..........Area
         Currency.............string..........Currency
         Value................integer.........Value
         Parcel Type..........string..........Parcel Type
         Land Use.............string..........Land Use
         Dispute..............string..........Dispute
         Comments.............string..........Comments
         WKT..................string..........Polygon

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="parcel_type" match="row" use="col[@field='Parcel Type']"/>
    <xsl:key name="landuse" match="row" use="col[@field='Land Use']"/>
    <xsl:key name="dispute" match="row" use="col[@field='Dispute']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Parcel Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('parcel_type',
                                                                       col[@field='Parcel Type'])[1])]">
                <xsl:call-template name="ParcelType"/>
            </xsl:for-each>

            <!-- Land Use -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('landuse',
                                                                       col[@field='Land Use'])[1])]">
                <xsl:call-template name="LandUse"/>
            </xsl:for-each>

            <!-- Disputes -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('dispute',
                                                                       col[@field='Dispute'])[1])]">
                <xsl:call-template name="Dispute"/>
            </xsl:for-each>

            <!-- Process all table rows for Structure records -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="stdm_parcel">
            <data field="name"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="area"><xsl:value-of select="col[@field='Area']"/></data>
            <data field="currency"><xsl:value-of select="col[@field='Currency']"/></data>
            <data field="value"><xsl:value-of select="col[@field='Value']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Link to Parcel Type -->
            <reference field="parcel_type_id" resource="stdm_parcel_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Parcel Type']"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Land Use -->
            <reference field="landuse_id" resource="stdm_landuse">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Land Use']"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Dispute -->
            <reference field="dispute_id" resource="stdm_dispute">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Dispute']"/>
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
    <xsl:template name="ParcelType">
        <xsl:variable name="type" select="col[@field='Parcel Type']/text()"/>

        <resource name="stdm_parcel_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$type"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$type"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LandUse">
        <xsl:variable name="type" select="col[@field='Land Use']/text()"/>

        <resource name="stdm_landuse">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$type"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$type"/></data>
       </resource>

    </xsl:template>
    <!-- ****************************************************************** -->
    <xsl:template name="Dispute">
        <xsl:variable name="type" select="col[@field='Dispute']/text()"/>

        <resource name="stdm_dispute">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$type"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$type"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
