<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:kml="http://www.opengis.net/kml/2.2"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         KML Import Templates for Sahana-Eden

         http://schemas.opengis.net/kml/2.2.0/
         http://code.google.com/apis/kml/documentation/kmlreference.html

         Version 0.2 / 2011-03-28 / by flavour

         Copyright (c) 2011 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    *********************************************************************** -->
    <xsl:output method="xml" indent="yes"/>
    <!--<xsl:include href="../xml/commons.xsl"/>-->

    <!-- Which Resource? -->
    <xsl:param name="name"/>

    <!-- Source URL for Feed caching -->
    <xsl:param name="source_url"/>
    <!-- Data element for Feed caching -->
    <xsl:param name="data_field"/>
    <!-- Image element for Feed caching -->
    <xsl:param name="image_field"/>

    <!-- Which mode?
        Simple mode: Name field from Placemark Name (default) & Comments from Details
        Extended mode: Name field from ExtendedData & Comments from Notes
    -->
    <xsl:param name="xsltmode"/>

    <!-- Which Country? (2-letter ISO) -->
    <xsl:param name="country"/>

    <!-- Location Hierarchy fieldnames -->
    <!--<xsl:choose>
        <xsl:when test="$country='jp'">-->
            <!-- Currently set to those for the Japan Shelters feed -->
            <xsl:variable name="L1">Prefecture</xsl:variable>
            <xsl:variable name="L2">City</xsl:variable>
            <xsl:variable name="L3">District</xsl:variable>
            <xsl:variable name="L4">__Dummy__</xsl:variable>
        <!--</xsl:when>
        <xsl:otherwise>
            <xsl:variable name="L1">Province</xsl:variable>
            <xsl:variable name="L2">District</xsl:variable>
            <xsl:variable name="L3">Town</xsl:variable>
            <xsl:variable name="L4">Village</xsl:variable>
        </xsl:otherwise>
    </xsl:choose>-->

    <xsl:key
        name="L1"
        match="//kml:Placemark"
        use="./kml:ExtendedData/kml:Data[@name=$L1]/kml:value/text()"/>

    <xsl:key
        name="L2"
        match="//kml:Placemark"
        use="./kml:ExtendedData/kml:Data[@name=$L2]/kml:value/text()"/>

    <xsl:key
        name="L3"
        match="//kml:Placemark"
        use="./kml:ExtendedData/kml:Data[@name=$L3]/kml:value/text()"/>

    <xsl:key
        name="L4"
        match="//kml:Placemark"
        use="./kml:ExtendedData/kml:Data[@name=$L4]/kml:value/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:choose>
                <!-- Feeds Cache -->
                <xsl:when test="$name='cache'">
                    <xsl:call-template name="feed"/>
                </xsl:when>

                <!-- Hospitals -->
                <xsl:when test="$name='hospital'">
                    <xsl:call-template name="hospitals"/>
                </xsl:when>

                <!-- Shelters -->
                <xsl:when test="$name='shelter'">
                    <xsl:call-template name="shelters"/>
                </xsl:when>

                <!-- Default to Locations -->
                <xsl:otherwise>
                    <xsl:call-template name="locations"/>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Do the Locations Hierarchy -->
            <xsl:call-template name="L4"/>
            <xsl:call-template name="L3"/>
            <xsl:call-template name="L2"/>
            <xsl:call-template name="L1"/>

        </s3xml>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="feed">
        <xsl:for-each select="//kml:Placemark">
            <xsl:call-template name="cache"/>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="cache">
        <resource name="gis_cache">

            <!-- KML have no uids for Placemarks
            <xsl:attribute name="uuid">
                <xsl:value-of select="concat($source_url, '/', ./guid/text())"/>
            </xsl:attribute>
            -->

            <data field="title">
                <xsl:value-of select="./kml:name/text()"/>
            </data>
            <data field="description">
                <xsl:value-of select="./kml:description/text()"/>
            </data>
            <!--
            <data field="link">
                <xsl:value-of select="./link/text()"/>
            </data>
            -->
            <data field="data">
                <!-- @ToDo: Right-trim too -->
                <xsl:call-template name="left-trim">
                    <xsl:with-param name="s" select="./*[name()=$data_field]/text()"/>
                </xsl:call-template>
            </data>
            <data field="image">
                <!-- @ToDo: Right-trim too -->
                <xsl:call-template name="left-trim">
                    <xsl:with-param name="s" select="./*[name()=$image_field]/text()"/>
                </xsl:call-template>
            </data>
            <data field="lat">
                <xsl:call-template name="lat">
                    <xsl:with-param name="coordinate" select="./kml:Point/kml:coordinates/text()"/>
                </xsl:call-template>
            </data>
            <data field="lon">
                <xsl:call-template name="lon">
                    <xsl:with-param name="coordinate" select="./kml:Point/kml:coordinates/text()"/>
                </xsl:call-template>
            </data>
            <data field="source">
                <xsl:value-of select="$source_url"/>
            </data>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="hospitals">
        <xsl:for-each select="//kml:Placemark">
            <xsl:call-template name="hospital"/>
       </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="hospital">
        <resource name="hms_hospital">

            <data field="name">
                <xsl:value-of select="./kml:name/text()"/>
            </data>
            <data field="comments">
                <!-- @ToDo: Cleanup HTML? -->
                <xsl:value-of select="./kml:description/text()"/>
            </data>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="shelters">
        <xsl:for-each select="//kml:Placemark">
            <xsl:call-template name="shelter"/>
       </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="shelter">
        <resource name="cr_shelter">


            <xsl:choose>
                <xsl:when test="$xsltmode != 'extended'">
                    <data field="name">
                        <xsl:value-of select="./kml:name/text()"/>
                    </data>
                    <data field="comments">
                        <!-- @ToDo: Cleanup HTML? -->
                        <xsl:value-of select="./kml:description/text()"/>
                    </data>
                </xsl:when>
            </xsl:choose>

            <xsl:for-each select="./kml:ExtendedData">
                <xsl:call-template name="extended"/>
            </xsl:for-each>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="extended">
        <xsl:choose>
            <xsl:when test="$xsltmode='extended'">
                <!-- Format produced by Google Fusion
                e.g. Japan feed: http://www.google.com/intl/ja/crisisresponse/japanquake2011_shelter.kmz -->
                <xsl:for-each select="./kml:Data[@name='Name']">
                    <data field="name">
                        <xsl:call-template name="detail"/>
                    </data>
                </xsl:for-each>
                <xsl:for-each select="./kml:Data[@name='Notes']">
                    <data field="comments">
                        <xsl:call-template name="detail"/>
                    </data>
                </xsl:for-each>
            </xsl:when>
        </xsl:choose>
        <xsl:for-each select="./kml:Data[@name='Population']">
            <data field="population">
                <xsl:call-template name="integer"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Capacity']">
            <data field="capacity">
                <xsl:call-template name="integer"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Source']">
            <data field="source">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name=$L1]">
            <data field="L1">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name=$L2]">
            <data field="L2">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name=$L3]">
            <data field="L3">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name=$L4]">
            <data field="L4">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <!-- Date needs converting -->
        <!--
        <xsl:for-each select="./kml:Data[@name='UpdateDate']">
            <xsl:attribute name="modified_on">
                <xsl:call-template name="detail"/>
             </xsl:attribute>
        </xsl:for-each>
        -->

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="detail">
        <xsl:value-of select="./kml:value/text()"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="integer">
        <xsl:variable name="x">
            <xsl:value-of select="./kml:value/text()"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="floor($x)=number($x) and $x!='-'">
                <xsl:value-of select="$x"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="locations">
        <xsl:for-each select="//kml:Placemark">
            <xsl:call-template name="location"/>
       </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <resource name="gis_location">

            <xsl:choose>
                <xsl:when test="$xsltmode='extended'">
                    <data field="name">
                        <xsl:for-each select="./kml:ExtendedData/kml:Data[@name='Name']">
                            <xsl:call-template name="detail"/>
                        </xsl:for-each>
                    </data>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="./kml:ExtendedData/kml:Data[@name=$L1]/kml:value/text()"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <data field="name">
                        <xsl:value-of select="./kml:name/text()"/>
                    </data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Handle Points -->
            <xsl:for-each select="./kml:Point">
                <xsl:call-template name="point"/>
            </xsl:for-each>

            <!-- Handle Linestrings -->
            <!--
            <xsl:for-each select="./kml:LineString">
                <xsl:call-template name="linestring"/>
            </xsl:for-each>
            -->

            <!-- Handle Polygons -->
            <!--
            <xsl:for-each select="./kml:Polygon">
                <xsl:call-template name="polygon"/>
            </xsl:for-each>
            -->

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Locations Hierarchy -->
    <xsl:template name="L1">
            <xsl:variable name="unique-list" select="//kml:Placemark[not(kml:ExtendedData/kml:Data[@name=$L1]/kml:value=following::kml:ExtendedData/kml:Data[@name=$L1]/kml:value)]" />
            <xsl:for-each select="$unique-list">
                <xsl:variable name="Name" select="./kml:ExtendedData/kml:Data[@name=$L1]/kml:value/text()"/>
                <xsl:if test="$Name!=''">
                    <resource name="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Name"/>
                        </xsl:attribute>
                        <data field="name">
                            <xsl:value-of select="$Name"/>
                        </data>
                        <xsl:if test="$country">
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="uuid">
                                    <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                                    <xsl:call-template name="uppercase">
                                        <xsl:with-param name="string" select="$country"/>
                                    </xsl:call-template>
                                </xsl:attribute>
                            </reference>
                        </xsl:if>
                    </resource>
                </xsl:if>
            </xsl:for-each>
    </xsl:template>

    <xsl:template name="L2">
        <xsl:variable name="unique-list" select="//kml:Placemark[not(kml:ExtendedData/kml:Data[@name=$L2]/kml:value=following::kml:ExtendedData/kml:Data[@name=$L2]/kml:value)]" />
        <xsl:for-each select="$unique-list">
            <xsl:variable name="Name" select="./kml:ExtendedData/kml:Data[@name=$L2]/kml:value/text()"/>
            <xsl:if test="$Name!=''">
                <resource name="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Name"/>
                    </xsl:attribute>
                    <data field="name">
                        <xsl:value-of select="$Name"/>
                    </data>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="./kml:ExtendedData/kml:Data[@name=$L1]/kml:value/text()"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="L3">
        <xsl:variable name="unique-list" select="//kml:Placemark[not(kml:ExtendedData/kml:Data[@name=$L3]/kml:value=following::kml:ExtendedData/kml:Data[@name=$L3]/kml:value)]" />
        <xsl:for-each select="$unique-list">
            <xsl:variable name="Name" select="./kml:ExtendedData/kml:Data[@name=$L3]/kml:value/text()"/>
            <xsl:if test="$Name!=''">
                <resource name="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Name"/>
                    </xsl:attribute>
                    <data field="name">
                        <xsl:value-of select="$Name"/>
                    </data>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:choose>
                                <xsl:when test="$country='jp'">
                                    <!-- Special case for Japan: L3 goes direct to L1 -->
                                    <xsl:value-of select="./kml:ExtendedData/kml:Data[@name=$L1]/kml:value/text()"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="./kml:ExtendedData/kml:Data[@name=$L2]/kml:value/text()"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="L4">
        <xsl:variable name="unique-list" select="//kml:Placemark[not(kml:ExtendedData/kml:Data[@name=$L4]/kml:value=following::kml:ExtendedData/kml:Data[@name=$L4]/kml:value)]" />
        <xsl:for-each select="$unique-list">
            <xsl:variable name="Name" select="./kml:ExtendedData/kml:Data[@name=$L4]/kml:value/text()"/>
            <xsl:if test="$Name!=''">
                <resource name="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Name"/>
                    </xsl:attribute>
                    <data field="name">
                        <xsl:value-of select="$Name"/>
                    </data>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="./kml:ExtendedData/kml:Data[@name=$L3]/kml:value/text()"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="point">
        <data field="gis_feature_type">1</data>
        <data field="lat">
            <xsl:call-template name="lat">
                <xsl:with-param name="coordinate" select="./kml:coordinates/text()"/>
            </xsl:call-template>
        </data>
        <data field="lon">
            <xsl:call-template name="lon">
                <xsl:with-param name="coordinate" select="./kml:coordinates/text()"/>
            </xsl:call-template>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="linestring">
        <data field="gis_feature_type">2</data>
        <data field="wkt">
            <xsl:text>LINESTRING(</xsl:text>
            <!-- @ToDo Convert Coordinates to build WKT string -->
            <!-- http://code.google.com/apis/kml/documentation/kml_tut.html#paths -->
            <!-- http://en.wikipedia.org/wiki/Well-known_text -->
            <xsl:value-of select="./kml:coordinates/text()"/>
            <xsl:text>)</xsl:text>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="polygon">
        <data field="gis_feature_type">3</data>
        <data field="wkt">
            <xsl:text>POLYGON((</xsl:text>
            <!-- @ToDo Convert Coordinates to build WKT string -->
            <!-- http://code.google.com/apis/kml/documentation/kml_tut.html#polygons -->
            <!-- http://en.wikipedia.org/wiki/Well-known_text -->
            <xsl:value-of select="./kml:coordinates/text()"/>
            <xsl:text>))</xsl:text>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="lon">
        <xsl:param name="coordinate"/>
        <xsl:call-template name="left-trim">
            <xsl:with-param name="s" select="substring-before($coordinate, ',')"/>
        </xsl:call-template>
    </xsl:template>

    <xsl:template name="lat">
        <xsl:param name="coordinate"/>
        <xsl:choose>
            <xsl:when test="contains (substring-after($coordinate, ','), ',')">
                <!-- Altitude field present -->
                <xsl:value-of select="substring-before(substring-after($coordinate, ','), ',')"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- Altitude field not present -->
                <xsl:call-template name="right-trim">
                    <xsl:with-param name="s" select="substring-after($coordinate, ',')"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="left-trim">
      <xsl:param name="s" />
      <xsl:choose>
        <xsl:when test="substring($s, 1, 1) = ''">
          <xsl:value-of select="$s"/>
        </xsl:when>
        <xsl:when test="normalize-space(substring($s, 1, 1)) = ''">
          <xsl:call-template name="left-trim">
            <xsl:with-param name="s" select="substring($s, 2)" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$s" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <xsl:template name="right-trim">
      <xsl:param name="s" />
      <xsl:choose>
        <xsl:when test="substring($s, 1, 1) = ''">
          <xsl:value-of select="$s"/>
        </xsl:when>
        <xsl:when test="normalize-space(substring($s, string-length($s))) = ''">
          <xsl:call-template name="right-trim">
            <xsl:with-param name="s" select="substring($s, 1, string-length($s) - 1)" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$s" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- Convert a string to uppercase -->
    <xsl:template name="uppercase">
        <xsl:param name="string"/>
        <xsl:value-of select="translate($string,
            'abcdefghijklmnopqrstuvwxyzáéíóúàèìòùäöüåâêîôûãẽĩõũø',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÀÈÌÒÙÄÖÜÅÂÊÎÔÛÃẼĨÕŨØ')"/>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
