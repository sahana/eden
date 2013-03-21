<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Facility" select="concat(col[@field='Name']/text(), ' Fire Station')"/>

        <resource name="fire_station">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="phone"><xsl:value-of select="col[@field='Phone']"/></data>
            <data field="fax"><xsl:value-of select="col[@field='Fax']"/></data>
            <data field="email"><xsl:value-of select="col[@field='Email']"/></data>
            <data field="website"><xsl:value-of select="col[@field='Website']"/></data>
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid"><xsl:value-of select="$OrgName"/></xsl:attribute>
            </reference>
            <reference field="location_id" resource="gis_location">
                <xsl:attribute name="tuid"><xsl:value-of select="$Facility"/></xsl:attribute>
            </reference>
        </resource>

        <xsl:call-template name="Locations"/>
    </xsl:template>
    <!-- ****************************************************************** -->

    <xsl:template name="Locations">

        <xsl:variable name="Facility" select="concat(col[@field='Name']/text(), ' Fire Station')"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

        <!-- L0 location -->
        <!-- Cannot be updated, so would produce validation errors -->
        <!--
        <resource name="gis_location">
            <xsl:attribute name="uuid">
                <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                <xsl:call-template name="iso2countryname">
                    <xsl:with-param name="country" select="$l0"/>
                </xsl:call-template>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$l0"/></data>
            <data field="level"><xsl:text>L0</xsl:text></data>
        </resource>
        -->

        <!-- Country Code = UUID of the L0 Location -->
        <xsl:variable name="countrycode">
            <xsl:call-template name="countryname2iso">
                <xsl:with-param name="country" select="$l0"/>
            </xsl:call-template>
        </xsl:variable>

        <!--<xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>-->
        <xsl:variable name="country" select="'urn:iso:std:iso:3166:-1:code:PT'"/>

        <!-- L1 Location -->
        <xsl:if test="$l1!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l1"/>
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
                    <xsl:value-of select="$l2"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1"/>
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
                    <xsl:value-of select="$l3"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1"/>
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

        <!-- Facility Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Facility"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l3"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l2"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l1"/>
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
            <data field="name"><xsl:value-of select="$Facility"/></data>
            <xsl:if test="col[@field='Lat']!=''">
                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            </xsl:if>
            <data field="addr_street">
                <xsl:value-of select="concat(col[@field='Address'], ', ',
                                             col[@field='City'], ', ',
                                             col[@field='State'])"/>
            </data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
