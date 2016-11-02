<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Availability Slots - CSV Import Stylesheet

         CSV fields:
         OID.............................cap_alerting_authority.oid
         Organisation....................org_organisation.name
         Country.........................gis_location.L0 Name or ISO2
         Authorization...................cap_alerting_authority.authorization
         Feed URL........................cap_alerting_authority_links.feed_url (comman separated for multiple links)
         Forecast URL....................cap_alerting_authority_links.forecast_url (comman separated for multiple links)

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="organisation" match="row"
             use="col[@field='Organisation']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation" />
            </xsl:for-each>

            <!-- Alerting Authority -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="cap_alerting_authority">
            <!-- Alerting Authority data -->
            <xsl:if test="col[@field='Country']!=''">
                <xsl:variable name="l0">
                    <xsl:value-of select="col[@field='Country']"/>
                </xsl:variable>
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
                <data field="country">
                    <xsl:value-of select="$countrycode"/>
                </data>
            </xsl:if>
            <data field="oid"><xsl:value-of select="col[@field='OID']/text()"/></data>

            <xsl:variable name="Authorization" select="col[@field='Authorization']/text()"/>
            <xsl:if test="$Authorization">
                <data field="authorization"><xsl:value-of select="$Authorization"/></data>
            </xsl:if>

            <!-- Link to Organisation -->
            <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to URLs -->
            <xsl:variable name="FeedURL" select="normalize-space(col[@field='Feed URL']/text())"/>
            <xsl:variable name="ForecastURL" select="normalize-space(col[@field='Forecast URL']/text())"/>
            <xsl:if test="$FeedURL!=''">
                <xsl:call-template name="FeedURL">
                    <xsl:with-param name="url" select="$FeedURL" />
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="$ForecastURL!=''">
                <xsl:call-template name="ForecastURL">
                    <xsl:with-param name="url" select="$ForecastURL" />
                </xsl:call-template>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:if test="$OrgName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="FeedURL">
        <xsl:param name="url"/>
        <xsl:param name="listsep" select="','"/>
        
        <xsl:choose>
            <xsl:when test="contains($url, $listsep)">
                <xsl:call-template name="FeedURL">
                    <xsl:with-param name="url" select="substring-before($url, $listsep)"/>
                </xsl:call-template>
                <xsl:call-template name="FeedURL">
                    <xsl:with-param name="url" select="substring-after($url, $listsep)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <resource name="cap_authority_feed_url">
                    <data field="url">
                        <xsl:value-of select="$url" />
                    </data>
                </resource>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ForecastURL">
        <xsl:param name="url"/>
        <xsl:param name="listsep" select="','"/>
        
        <xsl:choose>
            <xsl:when test="contains($url, $listsep)">
                <xsl:call-template name="ForecastURL">
                    <xsl:with-param name="url" select="substring-before($url, $listsep)"/>
                </xsl:call-template>
                <xsl:call-template name="ForecastURL">
                    <xsl:with-param name="url" select="substring-after($url, $listsep)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <resource name="cap_authority_forecast_url">
                    <data field="url">
                        <xsl:value-of select="$url" />
                    </data>
                </resource>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
