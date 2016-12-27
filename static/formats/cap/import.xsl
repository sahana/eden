<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2">

    <!-- **********************************************************************

         CAP Import Templates for Sahana Eden

         Copyright (c) 2011-16 Sahana Software Foundation

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
            <xsl:attribute name="uuid">
                <xsl:text>urn:uuid:</xsl:text>
                <xsl:value-of select="cap:identifier" />
            </xsl:attribute>
            <!-- All Imported CAP files are auto-approved -->
            <xsl:attribute name="approved">
                <xsl:text>true</xsl:text>
            </xsl:attribute>

            <data field="is_template">false</data>
            <xsl:if test="cap:identifier!=''">
                <data field="identifier">
                    <xsl:value-of select="cap:identifier" />
                </data>
            </xsl:if>
            <xsl:if test="cap:sender!=''">
                <data field="sender">
                    <xsl:value-of select="cap:sender" />
                </data>
            </xsl:if>
            <xsl:if test="cap:sent!=''">
                <data field="sent">
                    <xsl:value-of select="cap:sent" />
                </data>
            </xsl:if>
            <xsl:if test="cap:status!=''">
                <data field="status">
                    <xsl:value-of select="cap:status" />
                </data>
            </xsl:if>
            <xsl:if test="cap:msgType!=''">
                <data field="msg_type">
                    <xsl:value-of select="cap:msgType" />
                </data>
            </xsl:if>
            <xsl:if test="cap:source!=''">
                <data field="source">
                    <xsl:value-of select="cap:source" />
                </data>
            </xsl:if>
            <xsl:if test="cap:scope!=''">
                <data field="scope">
                    <xsl:value-of select="cap:scope" />
                </data>
            </xsl:if>
            <xsl:if test="cap:restriction!=''">
                <data field="restriction">
                    <xsl:value-of select="cap:restriction" />
                </data>
            </xsl:if>
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
                            <xsl:for-each select="cap:code">
                                <xsl:text>&quot;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&quot;</xsl:text>
                                <xsl:if test="position()!=last()">
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:for-each>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <xsl:if test="cap:note!=''">
                <data field="note">
                    <xsl:value-of select="cap:note" />
                </data>
            </xsl:if>
            <xsl:if test="./cap:info/cap:event!=''">
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="./cap:info/cap:event" />
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- below two fields are further parsed in python code -->
            <xsl:if test="cap:references!=''">
                <data field="references">
                    <xsl:value-of select="cap:references" />
                </data>
            </xsl:if>
            <!-- ToDo
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
            <xsl:apply-templates select="./cap:info" />
        </resource>
        <xsl:apply-templates select="./cap:info/cap:event" />
    </xsl:template>

    <!-- ****************************************************************** -->
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

    <!-- ****************************************************************** -->
    <xsl:template match="cap:info">
        <resource name="cap_info">
            <xsl:if test="cap:language!=''">
                <data field="language">
                    <xsl:value-of select="cap:language" />
                </data>
            </xsl:if>
            <xsl:if test="cap:category!=''">
                <data field="category">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:for-each select="cap:category">
                            <xsl:text>&quot;</xsl:text>
                            <xsl:value-of select="."/>
                            <xsl:text>&quot;</xsl:text>
                            <xsl:if test="position()!=last()">
                                <xsl:text>,</xsl:text>
                            </xsl:if>
                        </xsl:for-each>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <xsl:if test="cap:event!=''">
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="cap:event" />
                    </xsl:attribute>
                </reference>
                <data field="event">
                    <xsl:value-of select="cap:event" />
                </data>
            </xsl:if>
            <xsl:if test="cap:responseType!=''">
                <data field="response_type">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:for-each select="cap:responseType">
                            <xsl:text>&quot;</xsl:text>
                            <xsl:value-of select="."/>
                            <xsl:text>&quot;</xsl:text>
                            <xsl:if test="position()!=last()">
                                <xsl:text>,</xsl:text>
                            </xsl:if>
                        </xsl:for-each>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <!-- @todo: priority No, don't. Priority is not in the spec. -->
            <!--
            <data field="priority">
                <xsl:value-of select="cap:priority" />
            </data>
            -->
            <xsl:if test="cap:urgency!=''">
                <data field="urgency">
                    <xsl:value-of select="cap:urgency" />
                </data>
            </xsl:if>
            <xsl:if test="cap:severity!=''">
                <data field="severity">
                    <xsl:value-of select="cap:severity" />
                </data>
            </xsl:if>
            <xsl:if test="cap:certainty!=''">
                <data field="certainty">
                    <xsl:value-of select="cap:certainty" />
                </data>
            </xsl:if>
            <xsl:if test="cap:audience!=''">
                <data field="audience">
                    <xsl:value-of select="cap:audience" />
                </data>
            </xsl:if>
            <xsl:if test="cap:eventCode!=''">
                <data field="event_code">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:for-each select="cap:eventCode">
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
            <xsl:if test="cap:effective!=''">
                <data field="effective">
                    <xsl:value-of select="cap:effective" />
                </data>
            </xsl:if>
            <xsl:if test="cap:onset!=''">
                <data field="onset">
                    <xsl:value-of select="cap:onset" />
                </data>
            </xsl:if>
            <xsl:if test="cap:expires!=''">
                <data field="expires">
                    <xsl:value-of select="cap:expires" />
                </data>
            </xsl:if>
            <xsl:if test="cap:senderName!=''">
                <data field="sender_name">
                    <xsl:value-of select="cap:senderName" />
                </data>
            </xsl:if>
            <xsl:if test="cap:headline!=''">
                <data field="headline">
                    <xsl:value-of select="cap:headline" />
                </data>
            </xsl:if>
            <xsl:if test="cap:description!=''">
                <data field="description">
                    <xsl:value-of select="cap:description" />
                </data>
            </xsl:if>
            <xsl:if test="cap:instruction!=''">
                <data field="instruction">
                    <xsl:value-of select="cap:instruction" />
                </data>
            </xsl:if>
            <xsl:if test="cap:web!=''">
                <data field="web">
                    <xsl:value-of select="cap:web" />
                </data>
            </xsl:if>
            <xsl:if test="cap:contact!=''">
                <data field="contact">
                    <xsl:value-of select="cap:contact" />
                </data>
            </xsl:if>
            <!--<xsl:if test="cap:parameter!=''">
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
            </xsl:if>-->
            <xsl:if test="cap:parameter!=''">
                <xsl:apply-templates select="cap:parameter" />
            </xsl:if>

            <xsl:apply-templates select="cap:resource" />
            <xsl:apply-templates select="cap:area" />
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:parameter">
        <resource name="cap_info_parameter">                    
            <data field="name">
                <xsl:value-of select="cap:valueName" />
            </data>
            <data field="value">
                <xsl:value-of select="cap:value" />
            </data>            
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:resource">
        <resource name="cap_resource">
            <xsl:if test="cap:resourceDesc!=''">
                <data field="resource_desc">
                    <xsl:value-of select="cap:resourceDesc" />
                </data>
            </xsl:if>
            <xsl:if test="cap:mimeType!=''">
                <data field="mime_type">
                    <xsl:value-of select="cap:mimeType" />
                </data>
            </xsl:if>
            <xsl:if test="cap:size!=''">
                <data field="size">
                    <xsl:value-of select="cap:size" />
                </data>
            </xsl:if>
            <xsl:if test="cap:uri!=''">
                <data field="uri">
                    <xsl:value-of select="cap:uri" />
                </data>
            </xsl:if>
            <xsl:if test="cap:derefUri!=''">
                <data field="deref_uri">
                    <xsl:value-of select="cap:derefUri" />
                </data>
            </xsl:if>
            <xsl:if test="cap:digest!=''">
                <data field="digest">
                    <xsl:value-of select="cap:digest" />
                </data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:area">
        <resource name="cap_area">
            <xsl:variable name="areaDesc">
                <xsl:if test="cap:areaDesc!=''">
                    <xsl:value-of select="cap:areaDesc" />
                </xsl:if>
            </xsl:variable>
            <xsl:if test="$areaDesc!=''">
                <data field="name">
                    <xsl:value-of select="$areaDesc" />
                </data>
            </xsl:if>
            <xsl:if test="cap:altitude!=''">
                <data field="altitude">
                    <xsl:value-of select="cap:altitude" />
                </data>
            </xsl:if>
            <xsl:if test="cap:ceiling!=''">
                <data field="ceiling">
                    <xsl:value-of select="cap:ceiling" />
                </data>
            </xsl:if>
	     <xsl:if test="cap:polygon!=''">
                 <xsl:apply-templates select="cap:polygon">
		     <xsl:with-param name="name" select="$areaDesc"/>
		 </xsl:apply-templates>
	     </xsl:if>
	     <xsl:if test="cap:circle!=''">
	         <xsl:apply-templates select="cap:circle">
	             <xsl:with-param name="name" select="$areaDesc"/>
	         </xsl:apply-templates>
	     </xsl:if>
            <xsl:apply-templates select="cap:geocode" />
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!--
        Circles: Currently there is no support for CIRCLESTRING in OpenLayers,
        so we store the unmodified circle data in a gis_location_tag.
        Eventually we hope to have CIRCULARSTRING support, so this does pass
        through xml_post_parse, which currently only extracts the circle center
        as the lat lon.
    -->
    <xsl:template match="cap:circle">
        <xsl:param name="name" />
        <xsl:variable name="value">
            <xsl:value-of select="./text()"/>
        </xsl:variable>
        <xsl:variable name="radius">
            <xsl:value-of select="substring-after($value, ' ')"/>
        </xsl:variable>

        <resource name="cap_area_location">
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <data field="gis_feature_type" value="1">Point</data>
                    <data field="name">
                        <xsl:choose>
                            <xsl:when test="string-length($name) > 128">
                                <!-- Truncate -->
                                <xsl:value-of select="substring($name, 0, 124)"/>
                                <xsl:text>...</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$name"/>
                            </xsl:otherwise>
                        </xsl:choose>
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
    </xsl:template>

    <!-- ****************************************************************** -->
    <!--
        Polygons: These get converted in an xml_post_parse function, and are
        passed in via a non-s3xml element.
    -->

    <xsl:template match="cap:polygon">
        <xsl:param name="name" />
        <resource name="cap_area_location">
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <data field="gis_feature_type" value="3">Polygon</data>
                    <!-- Only use a prefix of the name. -->
                    <data field="name">
                        <xsl:choose>
                            <xsl:when test="string-length($name) > 128">
                                <!-- Truncate -->
                                <xsl:value-of select="substring($name, 0, 124)"/>
                                <xsl:text>...</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$name"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </data>
                    <data field="wkt">
                        <xsl:text>POLYGON((</xsl:text>
                        <xsl:call-template name="Points">
                            <xsl:with-param name="points">
                                <xsl:value-of select="."/>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:text>))</xsl:text>
                    </data>
                </resource>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Points">
        <xsl:param name="points"/>
        <xsl:choose>
            <xsl:when test="contains($points,' ')">
                <xsl:variable name="point" select="substring-before($points,' ')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($points,' '))"/>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point">
                        <xsl:value-of select="$point"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>,</xsl:text>
                <xsl:call-template name="Points">
                    <xsl:with-param name="points">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point">
                        <xsl:value-of select="$points"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Point">
        <xsl:param name="point"/>
        <xsl:variable name="lat" select="substring-before($point,',')"/>
        <xsl:variable name="lon" select="substring-after($point,',')"/>
        <xsl:value-of select="concat($lon,' ',$lat)"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Geocodes -->
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
    
</xsl:stylesheet>
