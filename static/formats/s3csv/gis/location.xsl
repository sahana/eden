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
         L0.................L0 Name
         L0 KV:XX...........L0 Key,Value (Key = XX in column name, value = cell in row)
         L1.................L1 Name
         L1 KV:XX ..........L1 Key,Value (Key = XX in column name, value = cell in row)
         L2.................L2 Name
         L2 KV:XX ..........L2 Key,Value (Key = XX in column name, value = cell in row)
         L3.................L3 Name
         L3 KV:XX ..........L3 Key,Value (Key = XX in column name, value = cell in row)
         L4.................L4 Name
         L4 KV:XX ..........L4 Key,Value (Key = XX in column name, value = cell in row)
         For specific locations:
         Name...............Location Name
         KV:XX..............Key,Value
         For lowest-level specified:
         WKT................WKT
         Lat................Lat
         Lon................Lon
         lat_min............Bounding Box (optional)
         lat_max............
         lon_min............
         lon_max............
         Elevation..........Elevation    (optional)
         Population.........Population   (optional)

         Specify as many level of hierarchy as you need to ensure correct
         location within the hierarchy

         Note: If you want WKT field populated for all admin levels
         then you will need to run the import once per admin level, e.g.:
         TL_L1.csv (L2, L3, L4, Name all blank)
         TL_L2.csv (L3, L4, Name all blank)
         TL_L3.csv (L4, Name all blank)
         TL_L4.csv (Name all blank)
         
         Note that if there are duplicate names at a certain level, then you need to specify the Lx above that to discriminate
         
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
    <xsl:key name="L0" match="row"
             use="col[@field='L0']"/>
    <xsl:key name="L1" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'])"/>
    <xsl:key name="L2" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'])"/>
    <xsl:key name="L3" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'], '/',
                                                    col[@field='L3'])"/>
    <xsl:key name="L4" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'], '/',
                                                    col[@field='L3'], '/',
                                                    col[@field='L4'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- L0 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L0',
                                                                   col[@field='L0'])[1])]">
                <xsl:call-template name="L0"/>
            </xsl:for-each>

            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L1',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1']))[1])]">
                <xsl:call-template name="L1"/>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L2',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2']))[1])]">
                <xsl:call-template name="L2"/>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L3',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3']))[1])]">
                <xsl:call-template name="L3"/>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L4',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4']))[1])]">
                <xsl:call-template name="L4"/>
            </xsl:for-each>

            <!-- L0 / Specific Locations -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L0">

        <xsl:variable name="l0" select="col[@field='L0']/text()"/>
        <xsl:variable name="code" select="col[@field='ISO2']/text()"/>

        <xsl:if test="$l0!='' and $code!=''">

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="concat('urn:iso:std:iso:3166:-1:code:', $code)"/>
                </xsl:attribute>
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L1'] or col[@field='L2'] or col[@field='L3'] or col[@field='L4'] or col[@field='Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <data field="name"><xsl:value-of select="$l0"/></data>
                        <data field="level"><xsl:text>L0</xsl:text></data>
                        <xsl:choose>
                            <xsl:when test="col[@field='WKT']!=''">
                                <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>
                            </xsl:when>
                            <xsl:when test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='lat_min']!='' and col[@field='lat_max']!='' and col[@field='lon_min']!='' and col[@field='lon_max']!='' ">
                            <data field="lat_min"><xsl:value-of select="col[@field='lat_min']"/></data>
                            <data field="lon_min"><xsl:value-of select="col[@field='lon_min']"/></data>
                            <data field="lat_max"><xsl:value-of select="col[@field='lat_max']"/></data>
                            <data field="lon_max"><xsl:value-of select="col[@field='lon_max']"/></data>
                        </xsl:if>
                        <!-- Named Tags -->
                        <resource name="gis_location_tag">
                            <data field="tag">ISO2</data>
                            <data field="value"><xsl:value-of select="$code"/></data>
                        </resource>
                        <xsl:if test="col[@field='Population']!=''">
                            <resource name="gis_location_tag">
                                <data field="tag">population</data>
                                <data field="value"><xsl:value-of select="col[@field='Population']"/></data>
                            </resource>
                        </xsl:if>
                        <!-- Arbitrary Tags -->
                        <xsl:for-each select="col[starts-with(@field, 'L0 KV')]">
                            <xsl:call-template name="KeyValue"/>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="gis_location_tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:if test="col[@field='L1']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>

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
                    <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <!-- Parent to Country -->
                <xsl:if test="$countrycode!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <!-- Arbitrary Tags -->
                <xsl:for-each select="col[starts-with(@field, 'L1 KV')]">
                    <xsl:call-template name="KeyValue"/>
                </xsl:for-each>
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L2'] or col[@field='L3'] or col[@field='L4'] or col[@field='Name']">
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
                                <xsl:if test="col[@field='lat_min']!='' and col[@field='lat_max']!='' and col[@field='lon_min']!='' and col[@field='lon_max']!='' ">
                                    <data field="lat_min"><xsl:value-of select="col[@field='lat_min']"/></data>
                                    <data field="lon_min"><xsl:value-of select="col[@field='lon_min']"/></data>
                                    <data field="lat_max"><xsl:value-of select="col[@field='lat_max']"/></data>
                                    <data field="lon_max"><xsl:value-of select="col[@field='lon_max']"/></data>
                                </xsl:if>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <resource name="gis_location_tag">
                                <data field="tag">population</data>
                                <data field="value"><xsl:value-of select="col[@field='Population']"/></data>
                            </resource>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:if test="col[@field='L2']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>

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
                    <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
                <!-- Arbitrary Tags -->
                <xsl:for-each select="col[starts-with(@field, 'L2 KV')]">
                    <xsl:call-template name="KeyValue"/>
                </xsl:for-each>

                <!-- If this is the import level then add the details -->
                 <xsl:choose>
                    <xsl:when test="col[@field='L3'] or col[@field='L4'] or col[@field='Name']">
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
                                <xsl:if test="col[@field='lat_min']!='' and col[@field='lat_max']!='' and col[@field='lon_min']!='' and col[@field='lon_max']!='' ">
                                    <data field="lat_min"><xsl:value-of select="col[@field='lat_min']"/></data>
                                    <data field="lon_min"><xsl:value-of select="col[@field='lon_min']"/></data>
                                    <data field="lat_max"><xsl:value-of select="col[@field='lat_max']"/></data>
                                    <data field="lon_max"><xsl:value-of select="col[@field='lon_max']"/></data>
                                </xsl:if>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <resource name="gis_location_tag">
                                <data field="tag">population</data>
                                <data field="value"><xsl:value-of select="col[@field='Population']"/></data>
                            </resource>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:if test="col[@field='L3']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>

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
                    <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
                <!-- Arbitrary Tags -->
                <xsl:for-each select="col[starts-with(@field, 'L3 KV')]">
                    <xsl:call-template name="KeyValue"/>
                </xsl:for-each>

                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L4'] or col[@field='Name']">
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
                                <xsl:if test="col[@field='lat_min']!='' and col[@field='lat_max']!='' and col[@field='lon_min']!='' and col[@field='lon_max']!='' ">
                                    <data field="lat_min"><xsl:value-of select="col[@field='lat_min']"/></data>
                                    <data field="lon_min"><xsl:value-of select="col[@field='lon_min']"/></data>
                                    <data field="lat_max"><xsl:value-of select="col[@field='lat_max']"/></data>
                                    <data field="lon_max"><xsl:value-of select="col[@field='lon_max']"/></data>
                                </xsl:if>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <resource name="gis_location_tag">
                                <data field="tag">population</data>
                                <data field="value"><xsl:value-of select="col[@field='Population']"/></data>
                            </resource>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:if test="col[@field='L4']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>

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
                    <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
                <!-- Arbitrary Tags -->
                <xsl:for-each select="col[starts-with(@field, 'L4 KV')]">
                    <xsl:call-template name="KeyValue"/>
                </xsl:for-each>

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
                                <xsl:if test="col[@field='lat_min']!='' and col[@field='lat_max']!='' and col[@field='lon_min']!='' and col[@field='lon_max']!='' ">
                                    <data field="lat_min"><xsl:value-of select="col[@field='lat_min']"/></data>
                                    <data field="lon_min"><xsl:value-of select="col[@field='lon_min']"/></data>
                                    <data field="lat_max"><xsl:value-of select="col[@field='lat_max']"/></data>
                                    <data field="lon_max"><xsl:value-of select="col[@field='lon_max']"/></data>
                                </xsl:if>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="col[@field='Population']!=''">
                            <resource name="gis_location_tag">
                                <data field="tag">population</data>
                                <data field="value"><xsl:value-of select="col[@field='Population']"/></data>
                            </resource>
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
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="name" select="col[@field='Name']/text()"/>

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
        <xsl:if test="$name!=''">
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
                        <xsl:if test="col[@field='lat_min']!='' and col[@field='lat_max']!='' and col[@field='lon_min']!='' and col[@field='lon_max']!='' ">
                            <data field="lat_min"><xsl:value-of select="col[@field='lat_min']"/></data>
                            <data field="lon_min"><xsl:value-of select="col[@field='lon_min']"/></data>
                            <data field="lat_max"><xsl:value-of select="col[@field='lat_max']"/></data>
                            <data field="lon_max"><xsl:value-of select="col[@field='lon_max']"/></data>
                        </xsl:if>
                    </xsl:when>
                </xsl:choose>
                <xsl:if test="col[@field='Elevation']!=''">
                    <data field="elevation"><xsl:value-of select="col[@field='Elevation']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Population']!=''">
                    <resource name="gis_location_tag">
                        <data field="tag">population</data>
                        <data field="value"><xsl:value-of select="col[@field='Population']"/></data>
                    </resource>
                </xsl:if>
                <!-- Arbitrary Tags -->
                <xsl:for-each select="col[starts-with(@field, 'KV')]">
                    <xsl:call-template name="KeyValue"/>
                </xsl:for-each>
                <xsl:choose>
                    <xsl:when test="col[@field='L4']!=''">
                        <!-- Parent to L4 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>