<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:cap="urn:oasis:names:tc:emergency:cap:1.1">

    <!-- **********************************************************************

         CAP-1.1 Import Transformation Stylesheet for Sahana Eden
         (identical to CAP-1.2 stylesheet except for CAP namespace URI)

         Copyright (c) 2011-18 Sahana Software Foundation

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

    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="cap:alert"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:alert">
        <resource name="cap_alert">

            <!-- All imported CAP alerts are auto-approved -->
            <xsl:attribute name="approved">true</xsl:attribute>

            <!-- Imported CAP alerts aren't templates -->
            <data field="is_template">false</data>

            <xsl:apply-templates select="cap:identifier"/>
            <xsl:apply-templates select="cap:sender"/>
            <xsl:apply-templates select="cap:sent"/>
            <xsl:apply-templates select="cap:status"/>
            <xsl:apply-templates select="cap:msgType"/>
            <xsl:apply-templates select="cap:source"/>
            <xsl:apply-templates select="cap:scope"/>
            <xsl:apply-templates select="cap:restriction"/>

            <!--@ToDo-->
            <!--<xsl:if test="cap:addresses!=''">-->
                <!--<data field="addresses">--> <!-- further in python code -->
                    <!--<xsl:value-of select="cap:addresses" />
                </data>
            </xsl:if>-->

            <xsl:if test="cap:code!=''">
                <data field="codes">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:apply-templates select="cap:code"/>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>

            <xsl:apply-templates select="cap:note"/>

            <!-- @ToDo: disabled, replace with special cap:parameter
            <xsl:if test="./cap:info/cap:event!=''">
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="./cap:info/cap:event" />
                    </xsl:attribute>
                </reference>
            </xsl:if>
            -->

            <!-- below two fields are further parsed in python code -->
            <xsl:apply-templates select="cap:references"/>

            <!-- @ToDo
            <xsl:if test="cap:incidents!=''">
                <data field="incidents">
                    <xsl:variable name="value">
                        <xsl:call-template name="quote">
                            <xsl:with-param name="string" select="cap:incidents"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:attribute name="value">
                        <xsl:value-of select="concat('[', $value, ']')"/>
                    </xsl:attribute>
                </data>
            </xsl:if>
            -->

            <xsl:apply-templates select="cap:info"/>

        </resource>

        <!-- disabled, concept unclear
        <xsl:apply-templates select="./cap:info/cap:event"/>
        -->

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- disabled, concept unclear
    <xsl:template match="cap:event">

        <xsl:variable name="EventTypeName" select="./text()"/>

        <xsl:if test="$EventTypeName!=''">
            <resource name="event_event_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$EventTypeName" />
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$EventTypeName" />
                </data>
            </resource>
        </xsl:if>

    </xsl:template>
    -->

    <!-- ****************************************************************** -->
    <xsl:template match="cap:info">
        <resource name="cap_info">

            <xsl:apply-templates select="cap:language"/>

            <xsl:if test="cap:category!=''">
                <data field="category">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:apply-templates select="cap:category"/>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>

            <xsl:if test="cap:event!=''">
                <!-- disabled until fixed
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="cap:event" />
                    </xsl:attribute>
                </reference>
                -->
                <data field="event">
                    <xsl:value-of select="cap:event" />
                </data>
            </xsl:if>

            <xsl:if test="cap:responseType!=''">
                <data field="response_type">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:apply-templates select="cap:responseType"/>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>

            <xsl:apply-templates select="cap:urgency"/>
            <xsl:apply-templates select="cap:severity"/>
            <xsl:apply-templates select="cap:certainty"/>
            <xsl:apply-templates select="cap:audience"/>

            <xsl:if test="cap:eventCode!=''">
                <data field="event_code">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:apply-templates select="cap:eventCode"/>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>

            <xsl:apply-templates select="cap:effective"/>
            <xsl:apply-templates select="cap:onset"/>
            <xsl:apply-templates select="cap:expires"/>
            <xsl:apply-templates select="cap:senderName"/>
            <xsl:apply-templates select="cap:headline"/>
            <xsl:apply-templates select="cap:description"/>
            <xsl:apply-templates select="cap:instruction"/>
            <xsl:apply-templates select="cap:web"/>
            <xsl:apply-templates select="cap:contact"/>

            <!-- Replaced by cap_info_parameter component -->
            <!--
            <xsl:if test="cap:parameter!=''">
                <data field="parameter">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:for-each select="cap:parameter">
                                <xsl:text>{&quot;key&quot;: &quot;</xsl:text>
                                <xsl:value-of select="cap:valueName"/>
                                <xsl:text>&quot;, &quot;value&quot;: &quot;</xsl:text>
                                <xsl:value-of select="cap:value"/>
                                <xsl:text>&quot;}</xsl:text>
                                <xsl:if test="position()!=last()">
                                    <xsl:text>, </xsl:text>
                                </xsl:if>
                            </xsl:for-each>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            -->

            <!-- Process sub-elements of cap:info -->
            <xsl:apply-templates select="cap:parameter" />
            <xsl:apply-templates select="cap:resource" />
            <xsl:apply-templates select="cap:area" />

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Alert info parameters -->
    <xsl:template match="cap:parameter">

        <resource name="cap_info_parameter">
            <data field="name">
                <xsl:value-of select="normalize-space(cap:valueName)" />
            </data>
            <data field="value">
                <xsl:value-of select="normalize-space(cap:value)" />
            </data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Alert info resources -->
    <xsl:template match="cap:resource">

        <!-- Resource description and MIME type are required -->
        <xsl:variable name="resourceDesc" select="normalize-space(cap:resourceDesc/text())"/>
        <xsl:variable name="mimeType" select="normalize-space(cap:mimeType/text())"/>

        <xsl:if test="$resourceDesc!='' and $mimeType!=''">
            <resource name="cap_resource">

                <data field="resource_desc">
                    <xsl:value-of select="$resourceDesc"/>
                </data>
                <data field="mime_type">
                    <xsl:value-of select="$mimeType"/>
                </data>

                <xsl:apply-templates select="cap:size"/>
                <xsl:apply-templates select="cap:uri"/>
                <xsl:apply-templates select="cap:derefUri"/>
                <xsl:apply-templates select="cap:digest"/>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Alert info area -->
    <xsl:template match="cap:area">

        <!-- Area description is required -->
        <xsl:variable name="areaDesc">
            <xsl:value-of select="normalize-space(cap:areaDesc/text())"/>
        </xsl:variable>

        <xsl:if test="$areaDesc!=''">
            <resource name="cap_area">

                <data field="name">
                    <xsl:value-of select="$areaDesc" />
                </data>

                <xsl:apply-templates select="cap:altitude"/>
                <xsl:apply-templates select="cap:ceiling"/>

                <!-- Area can consist of multiple cap:polygon/cap:circle/cap:geocode -->

                 <xsl:apply-templates select="cap:polygon">
                    <xsl:with-param name="name" select="$areaDesc"/>
                </xsl:apply-templates>

                 <xsl:apply-templates select="cap:circle">
                     <xsl:with-param name="name" select="$areaDesc"/>
                 </xsl:apply-templates>

                <xsl:apply-templates select="cap:geocode"/>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Circles: Currently there is no support for CIRCLESTRING in OpenLayers,
         so we store the unmodified circle data in a gis_location_tag.
         Eventually we hope to have CIRCULARSTRING support, so this does pass
         through xml_post_parse, which currently only extracts the circle center
         as the lat lon.
    -->
    <xsl:template match="cap:circle">

        <!-- The area name -->
        <xsl:param name="name" />

        <!-- A circle is given in the format "lat,lon radius" -->

        <xsl:variable name="value">
            <xsl:value-of select="normalize-space(./text())"/>
        </xsl:variable>

        <xsl:if test="$value!=''">
            <xsl:variable name="radius">
                <xsl:value-of select="substring-after($value, ' ')"/>
            </xsl:variable>

            <resource name="cap_area_location">
                <reference field="location_id" resource="gis_location">
                    <resource name="gis_location">

                        <data field="gis_feature_type" value="1">Point</data>

                        <!-- Location names are limited to 128 chars -->
                        <data field="name">
                            <xsl:call-template name="Name128">
                                <xsl:with-param name="name" select="normalize-space($name)"/>
                            </xsl:call-template>
                        </data>

                        <data field="lat">
                            <xsl:value-of select="substring-before($value, ',')"/>
                        </data>
                        <data field="lon">
                            <xsl:value-of select="substring-after(substring-before($value, ' '), ',')"/>
                        </data>
                        <data field="radius">
                            <!-- Radius comes in as km, so convert to m -->
                            <xsl:value-of select="number($radius) * 1000"/>
                        </data>

                    </resource>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Polygons -->
    <xsl:template match="cap:polygon">

        <xsl:param name="name" />

        <xsl:variable name="value" select="normalize-space(./text())"/>

        <xsl:if test="$value!=''">

            <xsl:variable name="points">
                <xsl:call-template name="Points">
                    <xsl:with-param name="points" select="$value"/>
                </xsl:call-template>
            </xsl:variable>

            <resource name="cap_area_location">
                <reference field="location_id" resource="gis_location">
                    <resource name="gis_location">

                        <data field="gis_feature_type" value="3">Polygon</data>

                        <!-- Location names are limited to 128 chars -->
                        <data field="name">
                            <xsl:call-template name="Name128">
                                <xsl:with-param name="name" select="normalize-space($name)"/>
                            </xsl:call-template>
                        </data>

                        <data field="wkt">
                            <xsl:value-of select="concat('POLYGON((', $points, '))')"/>
                        </data>

                    </resource>
                </reference>
            </resource>

        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Area Geocodes -->
    <xsl:template match="cap:geocode">

        <resource name="cap_area_tag">
            <data field="tag">
                <xsl:value-of select="cap:valueName" />
            </data>
            <data field="value">
                <xsl:value-of select="cap:value" />
            </data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Language element must be sanitized -->
    <xsl:template match="cap:language">

        <xsl:variable name="language" select="normalize-space(./text())"/>
        <xsl:if test="$language!=''">
            <data field="language">
                <xsl:call-template name="LanguageTag">
                    <xsl:with-param name="language" select="$language"/>
                </xsl:call-template>
            </data>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- These elements are transformed into JSON string lists -->
    <xsl:template match="cap:code|cap:category|cap:responseType|cap:eventCode">

        <xsl:text>&quot;</xsl:text>
        <xsl:value-of select="normalize-space(./text())"/>
        <xsl:text>&quot;</xsl:text>
        <xsl:if test="position()!=last()">
            <xsl:text>,</xsl:text>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- These elements are copied verbatim (i.e. retaining all white space) -->
    <xsl:template match="cap:restriction|cap:note|cap:audience|
                         cap:description|cap:instruction|cap:contact|
                         cap:derefUri|cap:disgest">

        <xsl:variable name="value" select="./text()"/>
        <xsl:if test="normalize-space($value)!=''">
            <xsl:variable name="fieldname">
                <xsl:variable name="name">
                    <xsl:value-of select="local-name(.)"/>
                </xsl:variable>
                <xsl:value-of select="$name"/>
                <!-- If there are name differences between CAP element and DB field: -->
                <!-- <xsl:choose> -->
                    <!-- Field name differs from CAP element name -->
                    <!-- <xsl:when test="$name='capName'">field_name</xsl:when> -->
                    <!-- Field name same as CAP element name -->
                    <!-- <xsl:otherwise><xsl:value-of select="$name"/></xsl:otherwise> -->
                <!-- </xsl:choose> -->
            </xsl:variable>
            <xsl:if test="$fieldname!=''">
                <data>
                    <xsl:attribute name="field">
                        <xsl:value-of select="$fieldname"/>
                    </xsl:attribute>
                    <xsl:value-of select="$value"/>
                </data>
            </xsl:if>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- All other elements are copied with normalized space -->
    <xsl:template match="cap:*">

        <xsl:variable name="value" select="normalize-space(./text())"/>
        <xsl:if test="$value!=''">
            <xsl:variable name="fieldname">
                <xsl:variable name="name">
                    <xsl:value-of select="local-name(.)"/>
                </xsl:variable>
                <xsl:choose>
                    <!-- Field name differs from CAP element name -->
                    <xsl:when test="$name='msgType'">msg_type</xsl:when>
                    <xsl:when test="$name='senderName'">sender_name</xsl:when>
                    <!-- Field name same as CAP element name -->
                    <xsl:otherwise><xsl:value-of select="$name"/></xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:if test="$fieldname!=''">
                <data>
                    <xsl:attribute name="field">
                        <xsl:value-of select="$fieldname"/>
                    </xsl:attribute>
                    <xsl:value-of select="$value"/>
                </data>
            </xsl:if>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Helper to limit a name to 128 chars -->
    <xsl:template name="Name128">

        <xsl:param name="name"/>

        <xsl:choose>
            <xsl:when test="string-length($name) > 128">
                <!-- Truncate -->
                <xsl:value-of select="concat(substring($name, 0, 124), '...')"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- Use as-is -->
                <xsl:value-of select="$name"/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Helper to sanitize cap:language tags -->
    <xsl:template name="LanguageTag">

        <xsl:param name="language"/>

        <xsl:choose>
            <xsl:when test="contains($language, '-')">

                <xsl:variable name="variantSubTag" select="substring-after($language, '-')"/>
                <xsl:choose>

                    <xsl:when test="string-length($variantSubTag)=2">
                        <!-- ISO3166-alpha2 Country Code => transform to uppercase -->
                        <xsl:variable name="countryCode">
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string" select="$variantSubTag"/>
                            </xsl:call-template>
                        </xsl:variable>
                        <xsl:value-of select="concat(substring-before($language, '-'), '-', $countryCode)"/>
                    </xsl:when>

                    <xsl:otherwise>
                        <!-- Other exotic language variant sub-tag => drop -->
                        <xsl:value-of select="substring-before($language, '-')"/>
                    </xsl:otherwise>

                </xsl:choose>
            </xsl:when>

            <xsl:otherwise>
                <!-- Simple ISO639 language code => keep as-is -->
                <xsl:value-of select="$language"/>
            </xsl:otherwise>

        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Helper to represent multiple points in WKT -->
    <xsl:template name="Points">

        <xsl:param name="points"/>

        <!-- CAP polygon ($points) is a
             - space-delimited list of comma-separated "lat,lon" pairs, whereas
             WKT wants a
             - comma-delimited list of space-separated "lon lat" pairs.

             The Points/Point templates are to transform the former (CAP)
             into the latter (WKT) format.
        -->

        <xsl:choose>
            <xsl:when test="contains($points,' ')">
                <xsl:call-template name="Point">
                    <xsl:with-param name="point" select="substring-before($points, ' ')"/>
                </xsl:call-template>
                <xsl:text>,</xsl:text>
                <xsl:call-template name="Points">
                    <xsl:with-param name="points" select="substring-after($points, ' ')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point" select="$points"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Helper to represent a single point in WKT -->
    <xsl:template name="Point">

        <xsl:param name="point"/>

        <xsl:variable name="lat" select="substring-before($point, ',')"/>
        <xsl:variable name="lon" select="substring-after($point, ',')"/>
        <xsl:value-of select="concat($lon, ' ', $lat)"/>

    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>
