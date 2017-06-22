<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:s3="http://eden.sahanafoundation.org/wiki/S3">

    <!-- **********************************************************************
         GeoJSON Export Templates for Sahana Eden

         Copyright (c) 2012-16 Sahana Software Foundation

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
    <xsl:output method="xml"/>

    <s3:fields tables="gis_location" select="name,lat,lon"/>
    <s3:fields tables="gis_cache" select="lat,lon,title,description,link,data,image,marker"/>
    <s3:fields tables="gis_feature_query" select="lat,lon,popup_label,popup_url,marker_url,marker_height,marker_width,shape,size,colour,opacity"/>
    <s3:fields tables="gis_layer_shapefile" select=""/>
    <s3:fields tables="gis_layer_shapefile*" select="layer_id"/>
    <s3:fields tables="gis_theme_data" select="location_id,value"/>
    <!-- Need to be able to filter &/or style records -->
    <s3:fields tables="cms_series" select="name"/>
    <s3:fields tables="deploy_application" select="human_resource_id"/>
    <!--
    <s3:fields tables="event_event" select="event_type_id"/>
    <s3:fields tables="event_event_location" select="event_id"/>-->
    <s3:fields tables="event_incident_report_group" select="incident_report_id"/>
    <s3:fields tables="event_post_incident_type" select="incident_type_id,post_id"/>
    <s3:fields tables="event_task" select="task_id"/>
    <s3:fields tables="gis_location_tag" select="location_id,tag,value"/>
    <s3:fields tables="gis_poi" select="poi_type_id"/>
    <s3:fields tables="hms_status" select="hospital_id"/>
    <s3:fields tables="project_activity_activity_type" select="activity_id"/>
    <s3:fields tables="project_activity_group" select="activity_id"/>
    <s3:fields tables="project_activity_organisation" select="activity_id,organisation_id"/>
    <s3:fields tables="project_beneficiary_activity" select="activity_id"/>
    <s3:fields tables="project_sector_activity" select="activity_id"/>
    <s3:fields tables="stats_people_group" select="people_id"/>
    <s3:fields tables="stats_trained_group" select="trained_id"/>
    <s3:fields tables="supply_distribution" select="activity_id"/>
    <s3:fields tables="vehicle_vehicle" select="asset_id,vehicle_type_id"/>
    <s3:fields tables="vulnerability_evac_route_group" select="evac_route_id"/>
    <s3:fields tables="vulnerability_risk_group" select="risk_id"/>
    <s3:fields tables="vulnerability_risk_tag" select="risk_id"/>
    <s3:fields tables="ANY" select="location_id,site_id"/>

    <xsl:param name="prefix"/>
    <xsl:param name="name"/>

    <xsl:template match="/">
        <GeoJSON>
            <xsl:apply-templates select="s3xml"/>
        </GeoJSON>
    </xsl:template>

    <xsl:template match="s3xml">
        <!-- S3 Extensions -->
        <xsl:variable name="s3" select="@map"/>
        <!-- Skip empty resources -->
        <xsl:variable name="results" select="@results"/>
        <xsl:variable name="start" select="@start"/>
        <xsl:if test="$results &gt; 0 and (not($start) or $start &lt; $results)">
            <xsl:variable name="resource" select="concat($prefix, '_', $name)"/>
            <xsl:choose>
                <xsl:when test="$resource='gis_layer_shapefile'">
                    <xsl:apply-templates select="./resource[@name='gis_layer_shapefile']"/>
                </xsl:when>
                <xsl:when test="count(./resource[@name=$resource])=1 and (count(./resource[@name=$resource]/map[1]/geometry)=1 or count(./resource[@name=$resource]/map[1]/geometry)=0)">
                    <!-- A single Feature not a Collection -->
                    <xsl:apply-templates select="./resource[@name=$resource]"/>
                </xsl:when>
                <xsl:otherwise>
                    <type>FeatureCollection</type>
                    <!-- S3 Extensions -->
                    <xsl:if test="$s3">
                        <s3>
                            <xsl:value-of select="$s3"/>
                        </s3>
                    </xsl:if>
                    <xsl:for-each select="./resource[@name=$resource]">
                        <xsl:apply-templates select="."/>
                    </xsl:for-each>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="uuid" select="./@uuid"/>
        <xsl:variable name="geometry" select="./map[1]/geometry/@value"/>
        <xsl:variable name="attributes" select="./map[1]/@attributes"/>
        <features>
            <xsl:choose>
                <xsl:when test="//reference[@resource='gis_location' and @uuid=$uuid]">
                    <xsl:for-each select="//reference[@resource='gis_location' and @uuid=$uuid]">
                        <xsl:if test="not(../@name='gis_location')">
                            <xsl:apply-templates select=".."/>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:when>
                <xsl:when test="$geometry!='null'">
                    <!-- Use pre-prepared GeoJSON -->
                    <type>Feature</type>
                    <geometry>
                        <xsl:attribute name="value">
                            <xsl:value-of select="$geometry"/>
                        </xsl:attribute>
                    </geometry>
                    <properties>
                        <xsl:call-template name="Properties"/>
                    </properties>
                </xsl:when>
                <xsl:otherwise>
                    <type>Feature</type>
                    <geometry>
                        <type>
                            <xsl:text>Point</xsl:text>
                        </type>
                        <coordinates>
                            <xsl:value-of select="data[@field='lon']"/>
                        </coordinates>
                        <coordinates>
                            <xsl:value-of select="data[@field='lat']"/>
                        </coordinates>
                    </geometry>
                    <properties>
                        <xsl:call-template name="Properties"/>
                    </properties>
                </xsl:otherwise>
            </xsl:choose>
        </features>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_cache']">
        <!-- GeoRSS or KML origin -->
        <features>
            <type>Feature</type>
            <geometry>
                <type>
                    <xsl:text>Point</xsl:text>
                </type>
                <coordinates>
                    <xsl:value-of select="data[@field='lon']"/>
                </coordinates>
                <coordinates>
                    <xsl:value-of select="data[@field='lat']"/>
                </coordinates>
            </geometry>
            <properties>
                <name>
                    <xsl:value-of select="data[@field='title']"/>
                </name>
                <description>
                    <xsl:value-of select="data[@field='description']"/>
                </description>
                <!-- Used by GeoRSS origin -->
                <link>
                    <xsl:value-of select="data[@field='link']"/>
                </link>
                <data>
                    <xsl:value-of select="data[@field='data']"/>
                </data>
                <image>
                    <xsl:value-of select="data[@field='image']"/>
                </image>
                <!-- Used by KML origin -->
                <marker>
                    <xsl:value-of select="data[@field='marker']"/>
                </marker>
            </properties>
        </features>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_feature_query']">
        <!-- Feature Query -->
        <features>
            <type>Feature</type>
            <geometry>
                <type>
                    <xsl:text>Point</xsl:text>
                </type>
                <coordinates>
                    <xsl:value-of select="data[@field='lon']"/>
                </coordinates>
                <coordinates>
                    <xsl:value-of select="data[@field='lat']"/>
                </coordinates>
            </geometry>
            <properties>
                <popup>
                    <xsl:value-of select="data[@field='popup_label']"/>
                </popup>
                <url>
                    <xsl:value-of select="data[@field='popup_url']"/>
                </url>
                <xsl:choose>
                    <xsl:when test="data[@field='marker_url']/text()!=''">
                        <marker_url>
                            <xsl:value-of select="data[@field='marker_url']/text()"/>
                        </marker_url>
                        <marker_height>
                            <xsl:value-of select="data[@field='marker_height']/text()"/>
                        </marker_height>
                        <marker_width>
                            <xsl:value-of select="data[@field='marker_width']/text()"/>
                        </marker_width>
                    </xsl:when>
                    <xsl:otherwise>
                        <shape>
                            <xsl:value-of select="data[@field='shape']"/>
                        </shape>
                        <size>
                            <xsl:value-of select="data[@field='size']"/>
                        </size>
                        <colour>
                            <xsl:value-of select="data[@field='colour']"/>
                        </colour>
                        <xsl:if test="data[@field='opacity']!=''">
                            <opacity>
                                <xsl:value-of select="data[@field='opacity']"/>
                            </opacity>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </properties>
        </features>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_layer_shapefile']">
        <!-- Shapefile Layer -->
        <!-- @ToDo: Count Features (we can't rely on the header as that's for the main resource, which will always be 1) -->
        <type>FeatureCollection</type>
        <xsl:for-each select="./resource">
            <features>
                <xsl:variable name="geometry" select="map[1]/geometry/@value"/>
                <xsl:variable name="attributes" select="map[1]/@attributes"/>

                <type>Feature</type>
                <geometry>
                    <xsl:attribute name="value">
                        <!-- Use pre-prepared GeoJSON -->
                        <xsl:value-of select="$geometry"/>
                    </xsl:attribute>
                </geometry>
                <properties>
                    <xsl:if test="$attributes!=''">
                        <xsl:call-template name="Attributes">
                            <xsl:with-param name="attributes">
                                <xsl:value-of select="$attributes"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:if>
                </properties>
            </features>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_theme_data']">
        <!-- Theme Layer -->
        <xsl:variable name="geometry" select="./map[1]/geometry/@value"/>
        <xsl:variable name="name" select="reference[@field='location_id']/text()"/>
        <xsl:variable name="value" select="data[@field='value']"/>

        <features>
            <type>Feature</type>
            <geometry>
                <xsl:attribute name="value">
                    <!-- Use pre-prepared GeoJSON -->
                    <xsl:value-of select="$geometry"/>
                </xsl:attribute>
            </geometry>
            <properties>
                <id>
                    <xsl:value-of select="substring-after(@uuid, 'urn:uuid:')"/>
                </id>
                <name>
                    <xsl:value-of select="$name"/>
                </name>
                <value>
                    <xsl:value-of select="$value"/>
                </value>
                <popup>
                    <xsl:value-of select="concat($name, ': ', $value)"/>
                </popup>
            </properties>
        </features>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <!-- Feature Layer -->
        <xsl:variable name="geometry" select="./map[1]/geometry/@value"/>
        <xsl:variable name="attributes" select="./map[1]/@attributes"/>
        <xsl:variable name="id" select="@id"/>
        <xsl:variable name="marker" select="./map[1]/@marker"/>
        <xsl:variable name="marker_url" select="./map[1]/@marker_url"/>
        <xsl:variable name="marker_height" select="./map[1]/@marker_height"/>
        <xsl:variable name="marker_width" select="./map[1]/@marker_width"/>
        <xsl:variable name="style" select="./map[1]/style/@value"/>

        <xsl:variable name="resource" select="@name"/>
        <xsl:variable name="NumberOfFeatures" select="count(//resource[@name=$resource])"/>

        <xsl:choose>
            <xsl:when test="$geometry!='null'">
                <!-- Use pre-prepared GeoJSON -->
                <xsl:choose>
                    <xsl:when test="$NumberOfFeatures=1 and count(./map[1]/geometry)=1">
                        <type>Feature</type>
                        <geometry>
                            <xsl:attribute name="value">
                                <xsl:value-of select="./map[1]/geometry/@value"/>
                            </xsl:attribute>
                        </geometry>
                        <properties>
                            <xsl:call-template name="Properties">
                                <xsl:with-param name="attributes">
                                    <xsl:value-of select="$attributes"/>
                                </xsl:with-param>
                                <xsl:with-param name="id">
                                    <xsl:value-of select="$id"/>
                                </xsl:with-param>
                                <xsl:with-param name="marker">
                                    <xsl:value-of select="$marker"/>
                                </xsl:with-param>
                                <xsl:with-param name="marker_url">
                                    <xsl:value-of select="$marker_url"/>
                                </xsl:with-param>
                                <xsl:with-param name="marker_height">
                                    <xsl:value-of select="$marker_height"/>
                                </xsl:with-param>
                                <xsl:with-param name="marker_width">
                                    <xsl:value-of select="$marker_width"/>
                                </xsl:with-param>
                                <xsl:with-param name="style">
                                    <xsl:value-of select="$style"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </properties>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:for-each select="./map[1]/geometry">
                            <features>
                                <type>Feature</type>
                                <geometry>
                                    <xsl:attribute name="value">
                                        <xsl:value-of select="./@value"/>
                                    </xsl:attribute>
                                </geometry>
                                <properties>
                                    <xsl:call-template name="Properties">
                                        <xsl:with-param name="attributes">
                                            <xsl:value-of select="$attributes"/>
                                        </xsl:with-param>
                                        <xsl:with-param name="id">
                                            <xsl:value-of select="$id"/>
                                        </xsl:with-param>
                                        <xsl:with-param name="marker">
                                            <xsl:value-of select="$marker"/>
                                        </xsl:with-param>
                                        <xsl:with-param name="marker_url">
                                            <xsl:value-of select="$marker_url"/>
                                        </xsl:with-param>
                                        <xsl:with-param name="marker_height">
                                            <xsl:value-of select="$marker_height"/>
                                        </xsl:with-param>
                                        <xsl:with-param name="marker_width">
                                            <xsl:value-of select="$marker_width"/>
                                        </xsl:with-param>
                                        <xsl:with-param name="style">
                                            <xsl:value-of select="$style"/>
                                        </xsl:with-param>
                                    </xsl:call-template>
                                </properties>
                            </features>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <!--
            <xsl:when test="./map[1]/@wkt!='null'">
                <xsl:call-template name="WKT">
                    <xsl:with-param name="wkt">
                        <xsl:value-of select="./map[1]/@wkt"/>
                    </xsl:with-param>
                    <xsl:with-param name="uuid">
                        <xsl:value-of select="./@uuid"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when> -->
            <xsl:when test="./map[1]/@lon!='null'">
                <!-- @ToDo: Support records with multiple locations
                            via making these also use the map element
                -->
                <xsl:choose>
                    <xsl:when test="$NumberOfFeatures=1">
                        <type>Feature</type>
                        <geometry>
                            <type>
                                <xsl:text>Point</xsl:text>
                            </type>
                            <coordinates>
                                <xsl:value-of select="./map[1]/@lon"/>
                            </coordinates>
                            <coordinates>
                                <xsl:value-of select="./map[1]/@lat"/>
                            </coordinates>
                        </geometry>
                        <properties>
                            <xsl:call-template name="Properties">
                                <xsl:with-param name="attributes">
                                    <xsl:value-of select="$attributes"/>
                                </xsl:with-param>
                                <xsl:with-param name="id">
                                    <xsl:value-of select="$id"/>
                                </xsl:with-param>
                                <xsl:with-param name="style">
                                    <xsl:value-of select="$style"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </properties>
                    </xsl:when>
                    <xsl:otherwise>
                        <features>
                            <type>Feature</type>
                            <geometry>
                                <type>
                                    <xsl:text>Point</xsl:text>
                                </type>
                                <coordinates>
                                    <xsl:value-of select="./map[1]/@lon"/>
                                </coordinates>
                                <coordinates>
                                    <xsl:value-of select="./map[1]/@lat"/>
                                </coordinates>
                            </geometry>
                            <properties>
                                <xsl:call-template name="Properties">
                                    <xsl:with-param name="attributes">
                                        <xsl:value-of select="$attributes"/>
                                    </xsl:with-param>
                                    <xsl:with-param name="id">
                                        <xsl:value-of select="$id"/>
                                    </xsl:with-param>
                                    <xsl:with-param name="style">
                                        <xsl:value-of select="$style"/>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </properties>
                        </features>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <!-- xsl:otherwise skip -->
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Properties">
        <xsl:param name="attributes"/>
        <xsl:param name="id"/>
        <xsl:param name="marker"/>
        <xsl:param name="marker_url"/>
        <xsl:param name="marker_height"/>
        <xsl:param name="marker_width"/>
        <xsl:param name="style"/>

        <xsl:if test="$marker!=''">
            <marker>
                <xsl:value-of select="$marker"/>
            </marker>
        </xsl:if>

        <xsl:if test="$marker_url!=''">
            <!-- Per-feature Marker -->
            <marker_url>
                <xsl:value-of select="$marker_url"/>
            </marker_url>
            <marker_height>
                <xsl:value-of select="$marker_height"/>
            </marker_height>
            <marker_width>
                <xsl:value-of select="$marker_width"/>
            </marker_width>
        </xsl:if>

        <!-- id is used for url_format -->
        <id>
            <!-- Numeric -->
            <xsl:attribute name="type">
                <xsl:text>numeric</xsl:text>
            </xsl:attribute>
            <xsl:value-of select="$id"/>
        </id>

        <xsl:if test="$style!=''">
            <!-- Use pre-prepared JSON -->
            <style>
                <xsl:attribute name="value">
                    <xsl:value-of select="$style"/>
                </xsl:attribute>
            </style>
        </xsl:if>

        <xsl:if test="$attributes!=''">
            <xsl:call-template name="Attributes">
                <xsl:with-param name="attributes">
                    <xsl:value-of select="$attributes"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Attribute">
        <xsl:param name="attribute"/>

        <xsl:variable name="key" select="substring-after(substring-before($attribute, '||::'), '||')"/>
        <xsl:variable name="value" select="substring-after($attribute, '||::')"/>
        <!--<xsl:if test="$key!=''">-->
            <xsl:element name="{$key}">
                <xsl:choose>
                    <xsl:when test="contains($value, '||')">
                        <!-- Text -->
                        <xsl:value-of select="substring-before(substring-after($value, '||'), '||')"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Numeric -->
                        <xsl:attribute name="type">
                            <xsl:text>numeric</xsl:text>
                        </xsl:attribute>
                        <xsl:value-of select="$value"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
        <!--</xsl:if>-->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Attributes">
        <xsl:param name="attributes"/>

        <xsl:variable name="attr">
            <xsl:choose>
                <xsl:when test="contains($attributes, '{{')">
                    <xsl:value-of select="substring-before(substring-after($attributes, '{{'), '}}')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$attributes"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="contains($attr, ',,||')">
                <xsl:variable name="attribute" select="substring-before($attr, ',,||')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($attr, ',,'))"/>
                <xsl:call-template name="Attribute">
                    <xsl:with-param name="attribute">
                        <xsl:value-of select="$attribute"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:call-template name="Attributes">
                    <xsl:with-param name="attributes">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Attribute">
                    <xsl:with-param name="attribute">
                        <xsl:value-of select="$attr"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="WKT">
        <xsl:param name="uuid"/>
        <xsl:param name="wkt"/>
        <!-- Convert WKT to GeoJSON in XSLT. Note that this can hit the libxslt default recursion limit
             http://blog.gmane.org/gmane.comp.python.lxml.devel/day=20120309
             This shouldn't be called any more but is left in as an example -->
        <type>Feature</type>
        <geometry>
            <xsl:choose>
                <xsl:when test="starts-with($wkt,'POINT')">
                    <type>
                        <xsl:text>Point</xsl:text>
                    </type>
                    <coordinates>
                        <xsl:attribute name="value">
                            <xsl:call-template name="Point">
                                <xsl:with-param name="point">
                                    <xsl:value-of select="substring-before(substring-after(normalize-space(substring-after($wkt,'POINT')),'('),')')"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:attribute>
                    </coordinates>
                </xsl:when>
                <xsl:when test="starts-with($wkt,'LINESTRING')">
                    <type>
                        <xsl:text>LineString</xsl:text>
                    </type>
                    <coordinates>
                        <xsl:attribute name="value">
                            <xsl:call-template name="LineString">
                                <xsl:with-param name="linestring">
                                    <xsl:value-of select="normalize-space(substring-after($wkt,'LINESTRING'))"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:attribute>
                    </coordinates>
                </xsl:when>
                <xsl:when test="starts-with($wkt,'POLYGON')">
                    <type>
                        <xsl:text>Polygon</xsl:text>
                    </type>
                    <coordinates>
                        <xsl:attribute name="value">
                            <xsl:call-template name="Polygon">
                                <xsl:with-param name="polygon">
                                    <xsl:value-of select="normalize-space(substring-after($wkt,'POLYGON'))"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:attribute>
                    </coordinates>
                </xsl:when>
                <xsl:when test="starts-with($wkt,'MULTIPOLYGON')">
                    <type>
                        <xsl:text>MultiPolygon</xsl:text>
                    </type>
                    <coordinates>
                        <xsl:attribute name="value">
                            <xsl:call-template name="MultiPolygon">
                                <xsl:with-param name="multipolygon">
                                    <xsl:value-of select="normalize-space(substring-after($wkt,'MULTIPOLYGON'))"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:attribute>
                    </coordinates>
                </xsl:when>
            </xsl:choose>
        </geometry>
        <properties>
            <xsl:call-template name="Properties">
                <xsl:with-param name="uuid">
                    <xsl:value-of select="$uuid"/>
                </xsl:with-param>
            </xsl:call-template>
        </properties>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Point">
        <xsl:param name="point"/>
        <xsl:variable name="lon" select="substring-before($point,' ')"/>
        <xsl:variable name="lat" select="substring-after($point,' ')"/>
        <xsl:value-of select="concat('[',$lon,', ',$lat,']')"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Points">
        <xsl:param name="points"/>
        <xsl:choose>
            <xsl:when test="contains($points,',')">
                <xsl:variable name="point" select="substring-before($points,',')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($points,','))"/>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point">
                        <xsl:value-of select="$point"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>, </xsl:text>
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
    <xsl:template name="LineString">
        <xsl:param name="linestring"/>
        <xsl:text>[</xsl:text>
        <!-- Strip outer parentheses -->
        <xsl:variable name="points" select="substring-before(substring-after($linestring,'('),')')"/>
        <xsl:call-template name="Points">
            <xsl:with-param name="points">
                <xsl:value-of select="$points"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Rings">
        <xsl:param name="rings"/>
        <xsl:choose>
            <xsl:when test="contains($rings,'),(')">
                <xsl:variable name="ring" select="substring-before($rings,',(')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($rings,'),'))"/>
                <xsl:call-template name="LineString">
                    <xsl:with-param name="linestring">
                        <xsl:value-of select="$ring"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>, </xsl:text>
                <xsl:call-template name="Rings">
                    <xsl:with-param name="rings">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="LineString">
                    <xsl:with-param name="linestring">
                        <xsl:value-of select="$rings"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Polygon">
        <xsl:param name="polygon"/>
        <xsl:text>[</xsl:text>
        <!-- Strip outer parentheses -->
        <xsl:variable name="rings" select="concat(substring-before(substring-after($polygon,'('),'))'),')')"/>
        <xsl:call-template name="Rings">
            <xsl:with-param name="rings">
                <xsl:value-of select="$rings"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Polygons">
        <xsl:param name="polygons"/>
        <xsl:choose>
            <xsl:when test="contains($polygons,'),(')">
                <xsl:variable name="polygon" select="substring-before($polygons,',(')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($polygons,'),'))"/>
                <xsl:call-template name="Polygon">
                    <xsl:with-param name="polygon">
                        <xsl:value-of select="$polygon"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>, </xsl:text>
                <xsl:call-template name="Polygons">
                    <xsl:with-param name="polygons">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Polygon">
                    <xsl:with-param name="polygon">
                        <xsl:value-of select="$polygons"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="MultiPolygon">
        <xsl:param name="multipolygon"/>
        <xsl:text>[</xsl:text>
        <!-- Strip outer parentheses -->
        <xsl:variable name="polygons" select="concat(substring-before(substring-after($multipolygon,'('),'))'),')')"/>
        <xsl:call-template name="Polygons">
            <xsl:with-param name="polygons">
                <xsl:value-of select="$polygons"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
    </xsl:template>

</xsl:stylesheet>
