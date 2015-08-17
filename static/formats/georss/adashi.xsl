<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:georss="http://www.georss.org/georss"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Import Templates for CAD GeoRSS Feeds (ADASHI)

         Copyright (c) 2015 Sahana Software Foundation

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
    <xsl:key name="incident_types" match="item" use="type/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template name="adashi">

        <xsl:choose>

            <xsl:when test="$category='AVL'">
                <!-- CAD Unit -->
                <xsl:call-template name="AdashiAVL"/>
            </xsl:when>

            <xsl:when test="$category='Incidents'">
                <!-- CAD Incident -->
                <xsl:call-template name="AdashiIncident"/>
            </xsl:when>

        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="adashiIncidentTypes">

        <xsl:for-each select="//item[generate-id(.)=generate-id(key('incident_types',
                                                                    type/text())[1])]">
            <xsl:variable name="TypeName" select="type/text()"/>
            <resource name="event_incident_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('IncidentType:', $TypeName)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="type/text()"/>
                </data>
            </resource>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiAVL">

        <xsl:variable name="UnitName" select="title/text()"/>
        <xsl:variable name="Lat" select="Y/text()"/>
        <xsl:variable name="Lon" select="X/text()"/>
        <xsl:variable name="Time" select="/rss/channel/pubDate/text()"/>

        <xsl:if test="$UnitName!='' and $Lat!='' and $Lon!='' and $Time!=''">
            <resource name="pr_group">

                <!-- Name -->
                <data field="name">
                    <xsl:value-of select="$UnitName"/>
                </data>

                <!-- Presence (location) -->
                <resource name="sit_presence">
                    <data field="timestmp">
                        <xsl:value-of select="$Time"/>
                    </data>
                    <reference resource="gis_location" field="location_id">
                        <resource name="gis_location">
                            <data field="lat">
                                <xsl:value-of select="$Lat"/>
                            </data>
                            <data field="lon">
                                <xsl:value-of select="$Lon"/>
                            </data>
                        </resource>
                    </reference>
                </resource>

                <!-- @todo: status -->

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiIncident">

        <xsl:variable name="IncidentName" select="incidentName/text()"/>
        <xsl:variable name="IncidentUID" select="incidentId/text()"/>
        <xsl:variable name="IncidentType" select="type/text()"/>

        <xsl:if test="$IncidentName!=''">

            <xsl:variable name="ZeroHour" select="started/text()"/>
            <xsl:variable name="ModifiedOn" select="lastModified/text()"/>
            <xsl:variable name="EndDate" select="ended/text()"/>

            <resource name="event_incident">

                <!-- UUID and modified_on -->
                <xsl:if test="$IncidentUID!=''">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$IncidentUID"/>
                    </xsl:attribute>
                </xsl:if>
                <xsl:if test="$ModifiedOn!=''">
                    <xsl:attribute name="modified_on">
                        <xsl:value-of select="$ModifiedOn"/>
                    </xsl:attribute>
                </xsl:if>

                <!-- Incident Name -->
                <data field="name">
                    <xsl:value-of select="$IncidentName"/>
                </data>
                <data field="exercise" value="False"/>

                <!-- Zero-hour -->
                <xsl:if test="$ZeroHour!=''">
                    <data field="zero_hour">
                        <xsl:value-of select="$ZeroHour"/>
                    </data>
                </xsl:if>

                <!-- Incident Type -->
                <xsl:if test="$IncidentType!=''">
                    <reference field="incident_type_id" resource="event_incident_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('IncidentType:', $IncidentType)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Location -->
                <reference resource="gis_location" field="location_id">
                    <xsl:call-template name="AdashiIncidentLocation"/>
                </reference>

                <!-- @todo: ended = needs implementation -->

                <!-- @todo: resources = event_team, needs implementation of component relationship first -->

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiIncidentLocation">

        <xsl:variable name="LocationName" select="addressName/text()"/>

        <xsl:variable name="Address1" select="address1/text()"/>
        <xsl:variable name="Address2" select="address2/text()"/>
        <xsl:variable name="Postcode" select="zip/text()"/>
        <xsl:variable name="StreetAddress">
            <xsl:choose>
                <xsl:when test="$Address1!='' and $Address2!=''">
                    <xsl:value-of select="concat($Address1, ', ', $Address2)"/>
                </xsl:when>
                <xsl:when test="$Address1!=''">
                    <xsl:value-of select="$Address1"/>
                </xsl:when>
                <xsl:when test="$Address2!=''">
                    <xsl:value-of select="$Address2"/>
                </xsl:when>
                <xsl:otherwise></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- @todo: indexed template for hierarchy locations, hierarchy location reference -->
        <xsl:variable name="L3" select="city/text()"/>
        <xsl:variable name="L1" select="state/text()"/>

        <xsl:variable name="LatLon" select="normalize-space(georss:point/text())"/>

        <!-- @todo: check that we have /any/ location data before creating a location -->
        <resource name="gis_location">

            <data field="name">
                <xsl:choose>
                    <xsl:when test="$LocationName!=''">
                        <xsl:value-of select="$LocationName"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="title/text()"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <xsl:if test="$StreetAddress!=''">
                <data field="addr_street">
                    <xsl:value-of select="$StreetAddress"/>
                </data>
            </xsl:if>
            <xsl:if test="$Postcode!=''">
                <data field="addr_postcode">
                    <xsl:value-of select="$Postcode"/>
                </data>
            </xsl:if>

            <xsl:if test="$LatLon">
                <data field="lat">
                    <xsl:value-of select="substring-before($LatLon, ' ')"/>
                </data>
                <data field="lon">
                    <xsl:value-of select="substring-after($LatLon, ' ')"/>
                </data>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
