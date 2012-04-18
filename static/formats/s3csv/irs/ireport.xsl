<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Incident Reports - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be hrm/competency_rating/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors

         CSV fields:
         Category.............string..........irs.ireport.category (needs to match irs_incident_type_opts)
         Name.................string..........irs_ireport.name
         Message..............string..........irs_ireport.message
         Date.................datetime........irs.ireport.datetime (ISO format: yyyy-mm-dd)
         Expiry...............datetime........irs_ireport.expiry
         Country..............string..........Country code/name (L0)
         State................string..........State/Province name (L1)
         District.............string..........District name (L2)
         City.................string..........City name (L3)
         Lat..................float...........Latitude  (Decimal Degrees)
         Lon..................float...........Longitude (Decimal Degrees)
         Image................string..........doc_image.url
         URL..................string..........doc_document.url
         Affected.............integer.........irs_ireport.affected
         Dead.................integer.........irs_ireport.dead
         Injured..............integer.........irs_ireport.injured

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- <xsl:key name="category" match="row" use="col[@field='Category']"/> -->

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Categories
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('category', col[@field='Category'])[1])]">
                <xsl:call-template name="Category"/>
            </xsl:for-each> -->

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Incident" select="col[@field='Name']/text()"/>
        <xsl:variable name="URL" select="col[@field='URL']/text()"/>
        <xsl:variable name="Image" select="col[@field='Image']/text()"/>

        <resource name="irs_ireport">
            <data field="category"><xsl:value-of select="col[@field='Category']"/></data>
            <data field="name"><xsl:value-of select="$Incident"/></data>
            <data field="message"><xsl:value-of select="col[@field='Message']"/></data>
            <data field="datetime"><xsl:value-of select="col[@field='Date']"/></data>
            <data field="expiry"><xsl:value-of select="col[@field='Expiry']"/></data>
            <data field="affected"><xsl:value-of select="col[@field='Affected']"/></data>
            <data field="dead"><xsl:value-of select="col[@field='Dead']"/></data>
            <data field="injured"><xsl:value-of select="col[@field='Injured']"/></data>

            <!-- Link to Location -->
            <xsl:call-template name="LocationReference"/>

            <!-- Image -->
            <xsl:if test="$Image!=''">
                <resource name="doc_image">
                    <data field="name"><xsl:value-of select="$Incident"/></data>
                    <data field="url"><xsl:value-of select="$Image"/></data>
                    <data field="file">
                        <xsl:attribute name="filename">
                            <xsl:call-template name="substringAfterLast">
                                <xsl:with-param name="input" select="$Image"/>
                                <xsl:with-param name="sep" select="'/'"/>
                            </xsl:call-template>
                        </xsl:attribute>
                        <xsl:attribute name="url">
                            <xsl:value-of select="$Image"/>
                        </xsl:attribute>
                    </data>
                </resource>
            </xsl:if>
            <!-- Document -->
            <xsl:if test="$URL!=''">
                <resource name="doc_document">
                    <data field="name"><xsl:value-of select="$Incident"/></data>
                    <data field="url"><xsl:value-of select="$URL"/></data>
                </resource>
            </xsl:if>
        </resource>

        <xsl:call-template name="Locations"/>

    </xsl:template>

    <!-- ****************************************************************** -->

    <!-- Unused
    <xsl:template match="Category">
        <xsl:variable name="CategoryName" select="col[@field='Category']/text()"/>

        <resource name="irs_icategory">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$CategoryName"/>
            </xsl:attribute>
            <data field="code"><xsl:value-of select="$CategoryName"/></data>
        </resource>

    </xsl:template> -->

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="Incident" select="col[@field='Name']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>

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

        <!-- L1 Location -->
        <xsl:if test="$l1!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l1id"/>
                </xsl:attribute>
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L2 Location -->
        <xsl:if test="$l2!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l2id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L3 Location -->
        <xsl:if test="$l3!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l3id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- Incident Location -->
        <xsl:if test="$Incident!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Incident"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l3id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$Incident"/></data>
                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">

        <xsl:variable name="Incident" select="col[@field='Name']/text()"/>

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>

        <xsl:choose>
            <xsl:when test="$Incident!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Incident"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>

            <xsl:when test="$l3!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l3id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l2!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l2id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l1!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l1id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l0!=''">
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
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
