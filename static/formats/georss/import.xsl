<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:georss="http://www.georss.org/georss"
    xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         GeoRSS Import Templates for Sahana-Eden

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

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:choose>
                <!-- Cache -->
                <xsl:when test="$name='cache'">
                    <xsl:call-template name="feed"/>
                </xsl:when>

                <!-- Default to Locations -->
                <xsl:otherwise>
                    <xsl:call-template name="locations"/>
                </xsl:otherwise>
            </xsl:choose>
        </s3xml>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="feed">
        <xsl:for-each select="//item">
            <xsl:call-template name="cache"/>
       </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="cache">
        <resource name="gis_cache">

            <xsl:attribute name="uuid">
                <xsl:value-of select="concat($source_url, '/', ./guid/text())"/>
            </xsl:attribute>

            <data field="title">
                <xsl:value-of select="./title/text()"/>
            </data>
            <data field="description">
                <xsl:value-of select="./description/text()"/>
            </data>
            <data field="link">
                <xsl:value-of select="./link/text()"/>
            </data>
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
            <xsl:choose>
                <xsl:when test="./georss:point/text() != ''">
                    <data field="lat">
                        <xsl:call-template name="lat">
                            <xsl:with-param name="latlon" select="./georss:point/text()"/>
                        </xsl:call-template>
                    </data>
                    <data field="lon">
                        <xsl:call-template name="lon">
                            <xsl:with-param name="latlon" select="./georss:point/text()"/>
                        </xsl:call-template>
                    </data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="lat">
                        <xsl:value-of select=".//geo:lat/text()"/>
                    </data>
                    <data field="lon">
                        <xsl:value-of select=".//geo:long/text()"/>
                    </data>
                </xsl:otherwise>
            </xsl:choose>
            <data field="source">
                <xsl:value-of select="$source_url"/>
            </data>

            <!-- Location Info (if using location_id FK)
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference> -->

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="locations">
        <xsl:for-each select="//item">
            <xsl:call-template name="location"/>
       </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <resource name="gis_location">

            <data field="name">
                <xsl:value-of select="./title/text()"/>
            </data>

            <data field="comments">
                <xsl:value-of select="./description/text()"/>
            </data>

            <!-- Handle Points -->
            <xsl:call-template name="point"/>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="point">
        <data field="gis_feature_type">1</data>
        <data field="lat">
            <xsl:call-template name="lat">
                <xsl:with-param name="latlon" select="./georss:point/text()"/>
            </xsl:call-template>
        </data>
        <data field="lon">
            <xsl:call-template name="lon">
                <xsl:with-param name="latlon" select="./georss:point/text()"/>
            </xsl:call-template>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="lat">
        <xsl:param name="latlon"/>
        <xsl:call-template name="left-trim">
            <xsl:with-param name="s" select="substring-before($latlon, ' ')"/>
        </xsl:call-template>
    </xsl:template>

    <xsl:template name="lon">
        <xsl:param name="latlon"/>
        <xsl:call-template name="right-trim">
            <xsl:with-param name="s" select="substring-after($latlon, ' ')"/>
        </xsl:call-template>
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

    <!-- ****************************************************************** -->

</xsl:stylesheet>
