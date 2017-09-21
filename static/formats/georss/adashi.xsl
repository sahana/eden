<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:georss="http://www.georss.org/georss"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Import Templates for CAD GeoRSS Feeds (ADASHI)

         Copyright (c) 2015-2017 Sahana Software Foundation

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
    <xsl:key name="cad_statuses" match="item" use="status/text()"/>

    <xsl:variable name="Namespace" select="'adashi'"/>
    <xsl:variable name="DefaultL0" select="'urn:iso:std:iso:3166:-1:code:US'"/>
    <xsl:variable name="ActiveStatus" select="'Active'"/>

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
    <xsl:template name="AdashiIncidentTypes">

        <xsl:for-each select="//item[generate-id(.)=generate-id(key('incident_types',
                                                                    type/text())[1])]">
            <xsl:variable name="TypeName" select="type/text()"/>
            <xsl:if test="$TypeName!=''">
                <resource name="event_incident_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('IncidentType:', $TypeName)"/>
                    </xsl:attribute>
                    <data field="name">
                        <xsl:value-of select="$TypeName"/>
                    </data>
                </resource>
            </xsl:if>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiCADStatuses">

        <xsl:for-each select="//item[generate-id(.)=generate-id(key('cad_statuses',
                                                                    status/text())[1])]">
            <xsl:variable name="StatusCode" select="status/text()"/>
            <xsl:if test="$StatusCode!=''">
                <resource name="pr_group_status">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('CADStatus:', $StatusCode)"/>
                    </xsl:attribute>
                    <data field="code">
                        <xsl:value-of select="$StatusCode"/>
                    </data>
                </resource>
            </xsl:if>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiAVL">

        <xsl:variable name="UnitName" select="title/text()"/>
        <xsl:variable name="StatusCode" select="status/text()"/>
        <xsl:variable name="Time">
            <xsl:choose>
                <xsl:when test="lastModified/text()!=''">
                    <xsl:value-of select="lastModified/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="/rss/channel/pubDate/text()"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$UnitName!='' and $Time!=''">
            <resource name="pr_group">

                <xsl:attribute name="modified_on">
                    <xsl:value-of select="$Time"/>
                </xsl:attribute>

                <!-- Name -->
                <data field="name">
                    <xsl:value-of select="$UnitName"/>
                </data>

                <!-- Status -->
                <xsl:if test="$StatusCode">
                    <reference field="status_id" resource="pr_group_status">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('CADStatus:', $StatusCode)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Presence (location) -->
                <xsl:variable name="LatLon" select="normalize-space(georss:point/text())"/>
                <xsl:variable name="Lat" select="Y/text()"/>
                <xsl:variable name="Lon" select="X/text()"/>
                <xsl:if test="$LatLon!='' or $Lat!='' and $Lon!=''">
                    <resource name="sit_presence">
                        <data field="timestmp">
                            <xsl:value-of select="$Time"/>
                        </data>
                        <reference resource="gis_location" field="location_id">
                            <resource name="gis_location">
                                <reference field="parent" resource="gis_location">
                                    <xsl:attribute name="uuid">
                                        <xsl:value-of select="$DefaultL0"/>
                                    </xsl:attribute>
                                </reference>
                                <xsl:choose>
                                    <xsl:when test="$LatLon!=''">
                                        <data field="lat">
                                            <xsl:value-of select="substring-before($LatLon, ' ')"/>
                                        </data>
                                        <data field="lon">
                                            <xsl:value-of select="substring-after($LatLon, ' ')"/>
                                        </data>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <data field="lat">
                                            <xsl:value-of select="$Lat"/>
                                        </data>
                                        <data field="lon">
                                            <xsl:value-of select="$Lon"/>
                                        </data>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </resource>
                        </reference>
                    </resource>
                </xsl:if>

            </resource>

            <!-- Status -->
            <xsl:if test="$StatusCode">
                <resource name="pr_group_status">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('CADStatus:', $StatusCode)"/>
                    </xsl:attribute>
                    <data field="code">
                        <xsl:value-of select="$StatusCode"/>
                    </data>
                </resource>
            </xsl:if>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiIncident">

        <xsl:variable name="IncidentDisplayName">
            <xsl:choose>
                <!-- Use incidentIdShort as display name -->
                <xsl:when test="incidentIdShort/text()!=''">
                    <xsl:value-of select="incidentIdShort/text()"/>
                </xsl:when>
                <!-- Fall back to item title if not present -->
                <xsl:otherwise>
                    <xsl:value-of select="title/text()"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="IncidentUID" select="incidentId/text()"/>
        <xsl:variable name="IncidentType" select="type/text()"/>

        <xsl:if test="$IncidentDisplayName!=''">

            <xsl:variable name="ZeroHour" select="started/text()"/>
            <xsl:variable name="ModifiedOn" select="lastModified/text()"/>
            <xsl:variable name="EndDate" select="ended/text()"/>

            <resource name="event_incident">

                <!-- UUID and modified_on -->
                <xsl:if test="$IncidentUID!=''">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="concat('urn:', $Namespace, ':incident:', $IncidentUID)"/>
                    </xsl:attribute>
                </xsl:if>
                <xsl:if test="$ModifiedOn!=''">
                    <xsl:attribute name="modified_on">
                        <xsl:value-of select="$ModifiedOn"/>
                    </xsl:attribute>
                </xsl:if>

                <!-- Incident Name -->
                <data field="name">
                    <xsl:value-of select="$IncidentDisplayName"/>
                </data>
                <data field="exercise" value="False"/>

                <!-- Zero-hour -->
                <xsl:if test="$ZeroHour!=''">
                    <data field="date">
                        <xsl:value-of select="$ZeroHour"/>
                    </data>
                </xsl:if>

                <!-- End date -->
                <xsl:if test="$EndDate!=''">
                    <data field="end_date">
                        <xsl:value-of select="$EndDate"/>
                    </data>
                    <!--  Assume that the incident is closed if it has an end
                          date. This could also be an onaccept to check whether
                          the end-date has actually passed - but what if not?
                          No regular system event that could reliably update the
                          "closed" flag when end_date arrives, and too complex
                          to implement one whilst ADASHI specifies that end-date
                          will only be present if it has already passed.
                    -->
                    <data field="closed" value="True"/>
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

                <!-- Units Assigned -->
                <xsl:variable name="Resources" select="resources/text()"/>
                <xsl:if test="$Resources!=''">
                    <xsl:call-template name="AdashiIncidentResources">
                        <xsl:with-param name="ModifiedOn">
                            <xsl:value-of select="$ModifiedOn"/>
                        </xsl:with-param>
                        <xsl:with-param name="Resources">
                            <xsl:value-of select="normalize-space($Resources)"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:if>

                <!-- Capture the incidentName in comments field -->
                <xsl:variable name="IncidentName" select="incidentName/text()"/>
                <xsl:if test="$IncidentName!=''">
                    <data field="comments">
                        <xsl:value-of select="$IncidentName"/>
                    </data>
                </xsl:if>

            </resource>

            <!-- Active Status for tuid match -->
            <resource name="event_team_status">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('UnitStatus:', $ActiveStatus)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$ActiveStatus"/>
                </data>
            </resource>

        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiIncidentLocation">

        <xsl:variable name="IncidentUID" select="incidentId/text()"/>
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

        <xsl:variable name="LatLon" select="normalize-space(georss:point/text())"/>

        <!-- L1/L3 available in feed, but inconsistent/invalid so can't easily be used here -->
        <!-- <xsl:variable name="L3" select="city/text()"/> -->
        <!-- <xsl:variable name="L1" select="state/text()"/> -->

        <xsl:if test="$LatLon!='' or $StreetAddress!=''">
            <resource name="gis_location">

                <!-- Add a UUID so that we don't create a new location record for every feed update -->
                <xsl:if test="$IncidentUID!=''">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="concat('urn:', $Namespace, ':incident:location:', $IncidentUID)"/>
                    </xsl:attribute>
                </xsl:if>

                <!-- Hardcoded parent location -->
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$DefaultL0"/>
                    </xsl:attribute>
                </reference>

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
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AdashiIncidentResources">

        <xsl:param name="ModifiedOn"/>
        <xsl:param name="Resources"/>
        <xsl:variable name="tail">
            <xsl:value-of select="substring-after($Resources, ' ')"/>
        </xsl:variable>
        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="$tail!=''">
                    <xsl:value-of select="substring-before($Resources, ' ')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$Resources"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="AdashiIncidentResources">
                <xsl:with-param name="ModifiedOn">
                    <xsl:value-of select="$ModifiedOn"/>
                </xsl:with-param>
                <xsl:with-param name="Resources">
                    <xsl:value-of select="$tail"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

        <xsl:if test="$head!=''">
            <resource name="event_team">
                <xsl:if test="$ModifiedOn!=''">
                    <xsl:attribute name="modified_on">
                        <xsl:value-of select="$ModifiedOn"/>
                    </xsl:attribute>
                </xsl:if>
                <reference field="group_id" resource="pr_group">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('ResponseUnit:', $head)"/>
                    </xsl:attribute>
                </reference>
                <!-- Status: Active -->
                <reference field="status_id" resource="event_team_status">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('UnitStatus:', $ActiveStatus)"/>
                    </xsl:attribute>
                </reference>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="item[resources/text()!='']" mode="generate-units">
        <xsl:call-template name="AdashiResponseUnits">
            <xsl:with-param name="Units">
                <xsl:value-of select="normalize-space(resources/text())"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template name="AdashiResponseUnits">

        <xsl:param name="Units"/>
        <xsl:variable name="tail">
            <xsl:value-of select="substring-after($Units, ' ')"/>
        </xsl:variable>
        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="$tail!=''">
                    <xsl:value-of select="substring-before($Units, ' ')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$Units"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="AdashiResponseUnits">
                <xsl:with-param name="Units">
                    <xsl:value-of select="normalize-space($tail)"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

        <xsl:if test="$head!='' and not(preceding-sibling::item[resources/text()!=''][
                contains(resources/text(), concat(' ', $head, ' ')) or
                starts-with(resources/text(), concat($head, ' ')) or
                contains(resources/text(), concat(' ', $head)) and substring-after(resources/text(), concat(' ', $head))=''
                ][1])">
            <resource name="pr_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('ResponseUnit:', $head)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$head"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
