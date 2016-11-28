<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         UAV Manufacturer - CSV Import Stylesheet

         CSV column...........Format..........Content
         Manufacturer.........string.........Name of the Manufacturer
         Name.................string.........Name of the Model

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="manufacturer" match="row"
             use="concat('Manufacturer:', col[@field='Manufacturer'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Manufacturer -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('manufacturer',
                                                        concat('Manufacturer:',
                                                               col[@field='Manufacturer']))[1])]">
                <xsl:call-template name="Manufacturer"/>
            </xsl:for-each>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="uav_model">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:variable name="Manufacturer" select="col[@field='Manufacturer']"/>
            <xsl:if test="$Manufacturer!=''">
                <reference field="manufacturer_id" resource="uav_manufacturer">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Manufacturer:', $Manufacturer)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Manufacturer">
    
        <xsl:variable name="Manufacturer" select="col[@field='Manufacturer']/text()"/>

        <xsl:if test="$Manufacturer!=''">
            <resource name="uav_manufacturer">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Manufacturer:', $Manufacturer)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$Manufacturer"/>
                </data>
            </resource>
        </xsl:if>
        
    </xsl:template>
    
    <!-- ****************************************************************** -->

</xsl:stylesheet>
