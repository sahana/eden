<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:cap = "urn:oasis:names:tc:emergency:cap:1.2">

    <!-- **********************************************************************

         CAP Import Templates for S3XRC

         Copyright (c) 2011-14 Sahana Software Foundation

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

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="cap:alert"/>
        </s3xml>
    </xsl:template>

    <!-- util -->
    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:alert">
        <resource name="cap_alert">
            <xsl:attribute name="uuid">
                <xsl:text>urn:uuid:</xsl:text>
                <xsl:value-of select="cap:identifier" />
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
            <xsl:if test="cap:addresses!=''">
                <data field="addresses"> <!-- further in python code -->
                    <xsl:value-of select="cap:addresses" />
                </data>
            </xsl:if>
            <xsl:if test="cap:alert/code!=''">
                <data field="code">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:for-each select="cap:alert/code">
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
            <xsl:if test="cap:category!=''">
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
            <xsl:if test="cap:parameter!=''">
                <data field="parameter">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:for-each select="cap:parameter">
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

            <xsl:apply-templates select="cap:resource" />
            <xsl:apply-templates select="cap:area" />
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
            <xsl:if test="cap:areaDesc!=''">
                <data field="area_desc">
                    <xsl:value-of select="cap:areaDesc" />
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
            <xsl:apply-templates select="cap:polygon" />
            <xsl:apply-templates select="cap:circle" />
            <xsl:apply-templates select="cap:geocode" />
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Polygons and circles: conversion to WKT will be done in Python. -->
    <xsl:template match="cap:polygon|cap:circle">
        <resource name="cap_area_location">
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <!-- Preserve unmodified polygon or circle text -->
                    <resource name="gis_location_tag">
                        <data field="tag">
                            <xsl:text>cap_</xsl:text>
                            <xsl:value-of select="local-name()" />
                        </data>
                        <data field="value">
                            <xsl:value-of select="./text()" />
                        </data>
                    </resource>
                </resource>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Circles: conversion to WKT will be done in Python. -->
    <xsl:template match="cap:circle">
        <resource name="cap_area_location">
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <!-- Preserve unmodified circle text -->
                    <resource name="gis_location_tag">
                        <data field="tag">
                            <xsl:text>cap_circle</xsl:text>
                        </data>
                        <data field="value">
                            <xsl:value-of select="./text()"/>
                        </data>
                    </resource>
                </resource>
            </reference>
        </resource>
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
