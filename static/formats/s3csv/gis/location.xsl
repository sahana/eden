<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Location - CSV Import Stylesheet

         - use for import to gis/location resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be org/organisation/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors

         CSV fields:
         Country.................L0 Country Name or ISO2
         ADM1_NAME...............L1 Name
         ADM1_CODE...............L1 Code
         ADM1_CODE2..............L1 Code2
         ADM2_NAME...............L2 Name
         ADM2_CODE...............L2 Code
         ADM2_CODE2..............L2 Code2
         ADM3_NAME...............L3 Name
         ADM3_CODE...............L3 Code
         ADM3_CODE2..............L3 Code2
         ADM4_NAME...............L4 Name
         ADM4_CODE...............L4 Code
         ADM4_CODE2..............L4 Code2
         Name....................gis_location.name       (for specific locations)
         Code....................gis_location.code       (for specific locations)
         Code2...................gis_location.code2      (for specific locations)
         WKT.....................gis_location.wkt
         Lat.....................gis_location.lat        (fallback if not WKT)
         Lon.....................gis_location.lon        (fallback if not WKT)
         Population..............gis_location.population (optional)
         Elevation...............gis_location.elevation  (optional)

         Specify as many level of hierarchy as you need to ensure correct
         location within the hierarchy

         Note: If you want WKT & Population fields populated for all admin levels
         then you will need to run the import once per admin level, e.g.:
         TL_L1.csv (ADM2_NAME, ADM3_NAME, ADM4_NAME, Name blank)
         TL_L2.csv (ADM3_NAME, ADM4_NAME, Name blank)
         TL_L3.csv (ADM4_NAME, Name blank)
         TL_L4.csv (Name blank)
         
    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Country">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Country</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="L1" match="row"
             use="concat(col[@field=$Country], '/', col[@field='ADM1_NAME'])"/>
    <xsl:key name="L2" match="row"
             use="concat(col[@field=$Country], '/', col[@field='ADM1_NAME'], '/', col[@field='ADM2_NAME'])"/>
    <xsl:key name="L3" match="row"
             use="concat(col[@field=$Country], '/', col[@field='ADM1_NAME'], '/', col[@field='ADM2_NAME'], '/', col[@field='ADM3_NAME'])"/>
    <xsl:key name="L4" match="row"
             use="concat(col[@field=$Country], '/', col[@field='ADM1_NAME'], '/', col[@field='ADM2_NAME'], '/', col[@field='ADM3_NAME'], '/', col[@field='ADM4_NAME'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L1',
                                                                   concat(col[@field=$Country], '/', col[@field='ADM1_NAME']))[1])]">
                <xsl:call-template name="L1"/>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L2',
                                                                   concat(col[@field=$Country], '/', col[@field='ADM1_NAME'], '/', col[@field='ADM2_NAME']))[1])]">
                <xsl:call-template name="L2"/>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L3',
                                                                   concat(col[@field=$Country], '/', col[@field='ADM1_NAME'], '/', col[@field='ADM2_NAME'], '/', col[@field='ADM3_NAME']))[1])]">
                <xsl:call-template name="L3"/>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L4',
                                                                   concat(col[@field=$Country], '/', col[@field='ADM1_NAME'], '/', col[@field='ADM2_NAME'], '/', col[@field='ADM3_NAME'], '/', col[@field='ADM4_NAME']))[1])]">
                <xsl:call-template name="L4"/>
            </xsl:for-each>

            <!-- L0 / Specific Locations -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:if test="col[@field='ADM1_NAME']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='ADM1_NAME']/text()"/>
            <xsl:variable name="code" select="col[@field='ADM1_CODE']/text()"/>
            <xsl:variable name="code2" select="col[@field='ADM1_CODE2']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
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

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($countrycode, $l1, $code, $code2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <xsl:if test="$code!=''">
                    <data field="code"><xsl:value-of select="$code"/></data>
                </xsl:if>
                <xsl:if test="$code2!=''">
                    <data field="code2"><xsl:value-of select="$code2"/></data>
                </xsl:if>
                <!-- Parent to Country -->
                <xsl:if test="$country!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='ADM2_NAME'] or col[@field='ADM3_NAME'] or col[@field='ADM4_NAME'] or col[@field='Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="col[@field='WKT']!=''">
                                <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                                <!-- Polygon
                                <data field="gis_feature_type"><xsl:text>3</xsl:text></data> -->
                            </xsl:when>
                            <xsl:when test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <data field="population"><xsl:value-of select="col[@field='Population']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:if test="col[@field='ADM2_NAME']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='ADM1_NAME']/text()"/>
            <xsl:variable name="l2" select="col[@field='ADM2_NAME']/text()"/>
            <xsl:variable name="l1code" select="col[@field='ADM1_CODE']/text()"/>
            <xsl:variable name="l1code2" select="col[@field='ADM1_CODE2']/text()"/>
            <xsl:variable name="code" select="col[@field='ADM2_CODE']/text()"/>
            <xsl:variable name="code2" select="col[@field='ADM2_CODE2']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
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

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($countrycode, $l1, $l2, $code, $code2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:if test="$code!=''">
                    <data field="code"><xsl:value-of select="$code"/></data>
                </xsl:if>
                <xsl:if test="$code2!=''">
                    <data field="code2"><xsl:value-of select="$code2"/></data>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="col[@field='ADM1_NAME']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($countrycode, $l1, $l1code, $l1code2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$country!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>

                <!-- If this is the import level then add the details -->
                 <xsl:choose>
                    <xsl:when test="col[@field='ADM3_NAME'] or col[@field='ADM4_NAME'] or col[@field='Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="col[@field='WKT']!=''">
                                <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                                <!-- Polygon
                                <data field="gis_feature_type"><xsl:text>3</xsl:text></data> -->
                            </xsl:when>
                            <xsl:when test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <data field="population"><xsl:value-of select="col[@field='Population']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:if test="col[@field='ADM3_NAME']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='ADM1_NAME']/text()"/>
            <xsl:variable name="l2" select="col[@field='ADM2_NAME']/text()"/>
            <xsl:variable name="l3" select="col[@field='ADM3_NAME']/text()"/>
            <xsl:variable name="l1code" select="col[@field='ADM1_CODE']/text()"/>
            <xsl:variable name="l1code2" select="col[@field='ADM1_CODE2']/text()"/>
            <xsl:variable name="l2code" select="col[@field='ADM2_CODE']/text()"/>
            <xsl:variable name="l2code2" select="col[@field='ADM2_CODE2']/text()"/>
            <xsl:variable name="code" select="col[@field='ADM3_CODE']/text()"/>
            <xsl:variable name="code2" select="col[@field='ADM3_CODE2']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
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

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($countrycode, $l1, $l2, $l3, $code, $code2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:if test="$code!=''">
                    <data field="code"><xsl:value-of select="$code"/></data>
                </xsl:if>
                <xsl:if test="$code2!=''">
                    <data field="code2"><xsl:value-of select="$code2"/></data>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="col[@field='ADM2_NAME']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($countrycode, $l1, $l2, $l2code, $l2code2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='ADM1_NAME']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($countrycode, $l1, $l1code, $l1code2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$country!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>

                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='ADM4_NAME'] or col[@field='Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="col[@field='WKT']!=''">
                                <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                                <!-- Polygon
                                <data field="gis_feature_type"><xsl:text>3</xsl:text></data> -->
                            </xsl:when>
                            <xsl:when test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <data field="population"><xsl:value-of select="col[@field='Population']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:if test="col[@field='ADM4_NAME']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='ADM1_NAME']/text()"/>
            <xsl:variable name="l2" select="col[@field='ADM2_NAME']/text()"/>
            <xsl:variable name="l3" select="col[@field='ADM3_NAME']/text()"/>
            <xsl:variable name="l4" select="col[@field='ADM4_NAME']/text()"/>
            <xsl:variable name="l1code" select="col[@field='ADM1_CODE']/text()"/>
            <xsl:variable name="l1code2" select="col[@field='ADM1_CODE2']/text()"/>
            <xsl:variable name="l2code" select="col[@field='ADM2_CODE']/text()"/>
            <xsl:variable name="l2code2" select="col[@field='ADM2_CODE2']/text()"/>
            <xsl:variable name="l3code" select="col[@field='ADM3_CODE']/text()"/>
            <xsl:variable name="l3code2" select="col[@field='ADM3_CODE2']/text()"/>
            <xsl:variable name="code" select="col[@field='ADM4_CODE']/text()"/>
            <xsl:variable name="code2" select="col[@field='ADM4_CODE2']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
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

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($countrycode, $l1, $l2, $l3, $l4, $code, $code2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:if test="$code!=''">
                    <data field="code"><xsl:value-of select="$code"/></data>
                </xsl:if>
                <xsl:if test="$code2!=''">
                    <data field="code2"><xsl:value-of select="$code2"/></data>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="col[@field='ADM3_NAME']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($countrycode, $l1, $l2, $l3, $l3code, $l3code2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='ADM2_NAME']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($countrycode, $l1, $l2, $l2code, $l2code2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='ADM1_NAME']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($countrycode, $l1, $l1code, $l1code2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$country!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>

                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="col[@field='WKT']!=''">
                                <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                                <!-- Polygon
                                <data field="gis_feature_type"><xsl:text>3</xsl:text></data> -->
                            </xsl:when>
                            <xsl:when test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <data field="population"><xsl:value-of select="col[@field='Population']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="l0">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Country"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="l1" select="col[@field='ADM1_NAME']/text()"/>
        <xsl:variable name="l2" select="col[@field='ADM2_NAME']/text()"/>
        <xsl:variable name="l3" select="col[@field='ADM3_NAME']/text()"/>
        <xsl:variable name="l4" select="col[@field='ADM4_NAME']/text()"/>
        <xsl:variable name="l1code" select="col[@field='ADM1_CODE']/text()"/>
        <xsl:variable name="l1code2" select="col[@field='ADM1_CODE2']/text()"/>
        <xsl:variable name="l2code" select="col[@field='ADM2_CODE']/text()"/>
        <xsl:variable name="l2code2" select="col[@field='ADM2_CODE2']/text()"/>
        <xsl:variable name="l3code" select="col[@field='ADM3_CODE']/text()"/>
        <xsl:variable name="l3code2" select="col[@field='ADM3_CODE2']/text()"/>
        <xsl:variable name="l4code" select="col[@field='ADM4_CODE']/text()"/>
        <xsl:variable name="l4code2" select="col[@field='ADM4_CODE2']/text()"/>
        <xsl:variable name="name" select="col[@field='Name']/text()"/>
        <xsl:variable name="code" select="col[@field='Code']/text()"/>
        <xsl:variable name="code2" select="col[@field='Code2']/text()"/>

        <!-- Country Code = UUID of the L0 Location -->
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

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <!-- Add the details -->
        <xsl:choose>
            <xsl:when test="$name!=''">
                <!-- Create the specific location -->
                <resource name="gis_location">
                    <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
                    <xsl:choose>
                        <xsl:when test="col[@field='WKT']!=''">
                            <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                            <!-- Polygon -->
                            <data field="gis_feature_type"><xsl:text>3</xsl:text></data>
                        </xsl:when>
                        <xsl:when test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                        </xsl:when>
                    </xsl:choose>
                    <xsl:if test="$code!=''">
                        <data field="code"><xsl:value-of select="$code"/></data>
                    </xsl:if>
                    <xsl:if test="$code2!=''">
                        <data field="code2"><xsl:value-of select="$code2"/></data>
                    </xsl:if>
                   <xsl:if test="col[@field='Population']!=''">
                        <data field="population"><xsl:value-of select="col[@field='Population']"/></data>
                    </xsl:if>
                    <xsl:if test="col[@field='Elevation']!=''">
                        <data field="elevation"><xsl:value-of select="col[@field='Elevation']"/></data>
                    </xsl:if>
                    <xsl:choose>
                        <xsl:when test="col[@field='ADM4_NAME']!=''">
                            <!-- Parent to L4 -->
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat($countrycode, $l1, $l2, $l3, $l4, $l4code, $l4code2)"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                        <xsl:when test="col[@field='ADM3_NAME']!=''">
                            <!-- Parent to L3 -->
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat($countrycode, $l1, $l2, $l3, $l3code, $l3code2)"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                        <xsl:when test="col[@field='ADM2_NAME']!=''">
                            <!-- Parent to L2 -->
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat($countrycode, $l1, $l2, $l2code, $l2code2)"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                        <xsl:when test="col[@field='ADM1_NAME']!=''">
                            <!-- Parent to L1 -->
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat($countrycode, $l1, $l1code, $l1code2)"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                        <xsl:when test="$country!=''">
                            <!-- Parent to Country -->
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="uuid">
                                    <xsl:value-of select="$country"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                    </xsl:choose>
                </resource>
            </xsl:when>
            <xsl:when test="col[@field='ADM1_NAME'] or col[@field='ADM2_NAME'] or col[@field='ADM3_NAME'] or col[@field='ADM4_NAME']">
            </xsl:when>
            <xsl:otherwise>
                <!-- Add WKT to the L0 location -->
                <xsl:if test="$countrycode!=''">
                    <resource name="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                        <xsl:if test="col[@field='WKT']!=''">
                            <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                            <!-- Polygon
                            <data field="gis_feature_type"><xsl:text>3</xsl:text></data> -->
                        </xsl:if>
                    </resource>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
