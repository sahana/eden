<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         UAV Manufacturer - CSV Import Stylesheet

         CSV column...........Format..........Content
         Name.................string.........Name of the Manufacturer
         Country..............string.........gis_location.L0 Name or ISO2

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="uav_manufacturer">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:if test="col[@field='Country']!=''">
                <xsl:variable name="l0">
                    <xsl:value-of select="col[@field='Country']"/>
                </xsl:variable>
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="string-length($l0)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$l0"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <data field="country">
                    <xsl:value-of select="$countrycode"/>
                </data>
            </xsl:if>
        </resource>
    </xsl:template>
    
    <!-- ****************************************************************** -->

</xsl:stylesheet>
