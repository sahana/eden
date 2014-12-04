<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         People - CSV Import Stylesheet

         CSV fields:
         Name.................................stats_people.name
         Type.................................stats_people.parameter_id
         Number...............................stats_people.value
         Contact First Name...................person_id.first_name
         Contact Last Name....................person_id.first_name
         Contact Phone........................person_id -> pr_contact.value
         Contact Email........................person_id -> pr_contact.value
         Organisation Group...................stats_people_group.group_id
         Address.................optional.....gis_location.addr_street
         Postcode................optional.....gis_location.addr_postcode
         Country.................optional.....gis_location.L0 Name or ISO2
         L1......................optional.....gis_location.L1
         L2......................optional.....gis_location.L2
         L3......................optional.....gis_location.L3
         Lat..................................gis_location.lat
         Lon..................................gis_location.lon
         WKT..................................gis_location.wkt
         Comments.............................stats_people.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Country">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Country</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Lat">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lat</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Lon">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lon</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Postcode">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Postcode</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>


    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="type" match="row" use="col[@field='Type']"/>
    <xsl:key name="organisation_group" match="row" use="col[@field='Organisation Group']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type',
                                                                       col[@field='Type'])[1])]">
                <xsl:call-template name="Type"/>
            </xsl:for-each>

            <!-- Organisation Groups -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation_group',
                                                                       col[@field='Organisation Group'])[1])]">
                <xsl:call-template name="OrganisationGroup"/>
            </xsl:for-each>

            <!-- People -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- People -->
        <resource name="stats_people">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="value"><xsl:value-of select="col[@field='Number']"/></data>
            
            <xsl:if test="col[@field='Type']!=''">
                <reference field="parameter_id" resource="stats_people_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Type:', col[@field='Type'])"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Person -->
            <xsl:if test="col[@field='Contact First Name']!=''">
                <reference field="person_id" resource="pr_person">
                    <resource name="pr_person">
                        <data field="first_name"><xsl:value-of select="col[@field='Contact First Name']"/></data>
                        <data field="last_name"><xsl:value-of select="col[@field='Contact Last Name']"/></data>
				        <xsl:if test="col[@field='Contact Email']!=''">
				            <resource name="pr_contact">
				                <data field="contact_method" value="EMAIL"/>
				                <data field="value">
				                    <xsl:value-of select="col[@field='Contact Email']/text()"/>
				                </data>
				            </resource>
				        </xsl:if>
				
				        <xsl:if test="col[@field='Contact Phone']!=''">
				            <resource name="pr_contact">
				                <data field="contact_method" value="HOME_PHONE"/>
				                <data field="value">
				                    <xsl:value-of select="col[@field='Contact Phone']/text()"/>
				                </data>
				            </resource>
				        </xsl:if>
                    </resource>
                </reference>
            </xsl:if>

            <!-- Organisation Group -->
            <xsl:if test="col[@field='Organisation Group']!=''">
                <resource name="stats_people_group">
	                <reference field="group_id" resource="org_group">
	                    <xsl:attribute name="tuid">
	                        <xsl:value-of select="concat('OrganisationGroup:', col[@field='Organisation Group'])"/>
	                    </xsl:attribute>
	                </reference>
                </resource>
            </xsl:if>

            <!-- Link to Location -->
            <reference field="location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Location:', col[@field='Address'], 
                                                              col[@field='Lat'], 
                                                              col[@field='Lon'],
                                                              col[@field='WKT'],
                                                              col[@field='L3']
                                                              )"/>
                </xsl:attribute>
            </reference>

            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

        </resource>
        
        <xsl:call-template name="Locations"/>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Type">

        <xsl:variable name="Type" select="col[@field='Type']"/>

        <xsl:if test="$Type!=''">
            <resource name="stats_people_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Type:', $Type)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Type"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrganisationGroup">

        <xsl:variable name="OrganisationGroup" select="col[@field='Organisation Group']"/>

        <xsl:if test="$OrganisationGroup!=''">
            <resource name="org_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('OrganisationGroup:', $OrganisationGroup)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrganisationGroup"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

   <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="wkt" select="col[@field='WKT']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="lon">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lon"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- Country Code = UUID of the L0 Location -->
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

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <!-- L1 Location -->
        <xsl:if test="$l1!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L1',$l1)"/>
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
                    <xsl:value-of select="concat('L2',$l2)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1',$l1)"/>
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
                    <xsl:value-of select="concat('L3',$l3)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2',$l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1',$l1)"/>
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

        <!-- L4 Location -->
        <xsl:if test="$l4!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L4',$l4)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3',$l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2',$l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1',$l1)"/>
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
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Location:', col[@field='Address'], 
                                                          $lat, 
                                                          $lon,
                                                          $wkt,
                                                          col[@field='L3'])"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L4',$l4)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L3',$l3)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L2',$l2)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L1',$l1)"/>
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
            <data field="addr_street"><xsl:value-of select="col[@field='Address']"/></data>
            <data field="addr_postcode"><xsl:value-of select="$postcode"/></data>
            <xsl:choose>
                <xsl:when test="$wkt!=''">
                    <data field="wkt"><xsl:value-of select="$wkt"/></data>
                </xsl:when>
                <xsl:when test="$lat!='' and $lon!=''">
                    <data field="lat"><xsl:value-of select="$lat"/></data>
                    <data field="lon"><xsl:value-of select="$lon"/></data>
                </xsl:when>
            </xsl:choose>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
