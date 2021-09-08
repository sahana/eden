<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Shelters - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Name...........................required.....cr_shelter.name
         Name L10n:XX...................org_site_name.name_10n (Language = XX in column name, name_10n = cell in row. Multiple allowed)
         Organisation...................org_organisation
         Branch.........................org_organisation[_branch]
         Type...........................shelter_type_id.name
         Service........................shelter_service_id.name (currently just supports 1)
         Country........................optional.....country
         L1.............................optional.....L1
         L2.............................optional.....L2
         L3.............................optional.....L3
         L4.............................optional.....L4
         L5.............................optional.....L5
         Building.......................optional.....gis_location.name (Name used if not-provided)
         Address........................optional.....Address
         Postcode.......................optional.....Postcode
         Lat............................optional.....Latitude
         Lon............................optional.....Longitude
         Capacity.......................cr_shelter.capacity_day (Only one used if not separated)
         Capacity Day...................cr_shelter.capacity_day
         Capacity Night.................cr_shelter.capacity_night
         Population.....................cr_shelter.population
         Status.........................cr_shelter.status (@ToDo: Populate cr_shelter_status for historical data)
         Obsolete.......................cr_shelter.obsolete
         Comments.......................cr_shelter.comments
         KV:XX..........................Key,Value (Key = XX in column name, value = cell in row)

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:param name="mode"/>

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
    <xsl:key name="L1" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'])"/>
    <xsl:key name="L2" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'])"/>
    <xsl:key name="L3" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'])"/>
    <xsl:key name="L4" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'])"/>

    <xsl:key name="L5" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'], '/',
                         col[@field='L5'])"/>

    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="branch" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>
    <xsl:key name="type" match="row" use="col[@field='Type']"/>
    <xsl:key name="service" match="row" use="col[@field='Service']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L1',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1']))[1])]">
                <xsl:call-template name="L1"/>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L2',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2']))[1])]">
                <xsl:call-template name="L2"/>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L3',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3']))[1])]">
                <xsl:call-template name="L3"/>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L4',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4']))[1])]">
                <xsl:call-template name="L4"/>
            </xsl:for-each>

            <!-- L5 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L5',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4'], '/',
                                                                          col[@field='L5']))[1])]">
                <xsl:call-template name="L5"/>
            </xsl:for-each>

            <!-- Top-level Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName"></xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Branches -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('branch', concat(col[@field='Organisation'], '/', col[@field='Branch']))[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName"></xsl:with-param>
                    <xsl:with-param name="BranchName">
                        <xsl:value-of select="col[@field='Branch']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type', col[@field='Type'])[1])]">
                <xsl:call-template name="Type"/>
            </xsl:for-each>

            <!-- Services -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('service', col[@field='Service'])[1])]">
                <xsl:call-template name="Service"/>
            </xsl:for-each>

            <!-- Process all table rows for shelter records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Shelter Record -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
        <xsl:variable name="ShelterName" select="col[@field='Name']/text()"/>
        <xsl:variable name="Type" select="col[@field='Type']/text()"/>
        <xsl:variable name="Service" select="col[@field='Service']/text()"/>
        <xsl:variable name="Status" select="col[@field='Status']/text()"/>
        <xsl:variable name="Capacity" select="col[@field='Capacity']/text()"/>
        <xsl:variable name="country">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Country"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$Building!='' or $addr_street!='' or $lat!=''">
            <!-- Specific Location -->
            <xsl:call-template name="Location"/>
        </xsl:if>

        <resource name="cr_shelter">
            <data field="name"><xsl:value-of select="$ShelterName"/></data>
            <xsl:choose>
                <xsl:when test="$Capacity!=''">
                    <data field="capacity_day"><xsl:value-of select="$Capacity"/></data>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="col[@field='Capacity Day']!=''">
                        <data field="capacity_day"><xsl:value-of select="col[@field='Capacity Day']"/></data>
                    </xsl:if>
                    <xsl:if test="col[@field='Capacity Night']!=''">
                        <data field="capacity_night"><xsl:value-of select="col[@field='Capacity Night']"/></data>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="col[@field='Population']!=''">
                <data field="population"><xsl:value-of select="col[@field='Population']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Obsolete']!=''">
                <data field="obsolete"><xsl:value-of select="col[@field='Obsolete']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <xsl:choose>
                <xsl:when test="$Status='Closed'">
                    <data field="status">1</data>
                </xsl:when>
                <xsl:when test="$Status='Open'">>
                    <data field="status">2</data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="status">
                        <xsl:value-of select="$Status"/>
                    </data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Link to Location -->
            <xsl:if test="$country!='' or $Building!='' or $addr_street!='' or $lat!=''">
                <xsl:call-template name="LocationReference"/>
            </xsl:if>

            <!-- Link to Organisation -->
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:choose>
                            <xsl:when test="$BranchName!=''">
                                <xsl:value-of select="concat($OrgName, $BranchName)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$OrgName"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Shelter Type -->
            <reference field="shelter_type_id" resource="cr_shelter_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Type"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Shelter Service -->
            <xsl:if test="$Service!=''">
                <resource name="cr_shelter_service_shelter">
                    <reference field="service_id" resource="cr_shelter_service">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Service"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- L10n -->
            <xsl:for-each select="col[starts-with(@field, 'Name L10n')]">
                <xsl:variable name="Lang" select="normalize-space(substring-after(@field, ':'))"/>
                <xsl:call-template name="L10n">
                    <xsl:with-param name="Lang">
                        <xsl:value-of select="$Lang"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Arbitrary Tags -->
            <xsl:for-each select="col[starts-with(@field, 'KV')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>

        </resource>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <!-- Create the Organisation/Branch -->
        <xsl:if test="$OrgName!='' or $BranchName!=''">
            <resource name="org_organisation">
                <xsl:choose>
                    <xsl:when test="$OrgName!=''">
                        <!-- This is the Organisation -->
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OrgName"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$OrgName"/></data>
                    </xsl:when>
                    <xsl:when test="$BranchName!=''">
                        <!-- This is the Branch -->
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat(col[@field='Organisation'],$BranchName)"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$BranchName"/></data>
                    </xsl:when>
                </xsl:choose>

                <xsl:if test="$BranchName!=''">
                    <!-- Nest the Top-Level -->
                    <!-- Don't create Orgs as Branches of themselves -->
                    <xsl:if test="col[@field='Organisation']!=$BranchName">
                        <resource name="org_organisation_branch" alias="parent">
                            <reference field="organisation_id">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="col[@field='Organisation']"/>
                                </xsl:attribute>
                            </reference>
                        </resource>
                    </xsl:if>
                </xsl:if>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Type">
        <xsl:variable name="type" select="col[@field='Type']/text()"/>

        <resource name="cr_shelter_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$type"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$type"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Service">
        <xsl:variable name="service" select="col[@field='Service']/text()"/>

        <resource name="cr_shelter_service">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$service"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$service"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="org_site_tag" alias="tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L10n">
        <xsl:param name="Lang"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="org_site_name">
                <data field="language"><xsl:value-of select="$Lang"/></data>
                <data field="name_l10n"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:if test="col[@field='L1']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>

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
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <!-- Parent to Country -->
                <xsl:if test="$countrycode!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:if test="col[@field='L2']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>

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
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:if test="col[@field='L3']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>

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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:if test="col[@field='L4']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>

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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L5">
        <xsl:if test="col[@field='L5']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>
            <xsl:variable name="l5" select="col[@field='L5']/text()"/>

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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l5"/></data>
                <data field="level"><xsl:text>L5</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L4']!=''">
                        <!-- Parent to L4 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">

        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$Building!='' or $addr_street!='' or $lat!=''">
                <!-- Specific Location -->
                <xsl:variable name="Name">
                    <xsl:choose>
                        <xsl:when test="$Building!=''">
                            <xsl:value-of select="$Building"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="col[@field='Name']/text()"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="lon">
                    <xsl:call-template name="GetColumnValue">
                        <xsl:with-param name="colhdrs" select="$Lon"/>
                    </xsl:call-template>
                </xsl:variable>
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location:', $Name, '/', $addr_street, '/', $lat, '/', $lon)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>

            <xsl:otherwise>
                <!-- Lx -->
                <xsl:variable name="l0">
                    <xsl:call-template name="GetColumnValue">
                        <xsl:with-param name="colhdrs" select="$Country"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="l1" select="col[@field='L1']/text()"/>
                <xsl:variable name="l2" select="col[@field='L2']/text()"/>
                <xsl:variable name="l3" select="col[@field='L3']/text()"/>
                <xsl:variable name="l4" select="col[@field='L4']/text()"/>
                <xsl:variable name="l5" select="col[@field='L5']/text()"/>

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
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string">
                                   <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <xsl:variable name="l1id" select="concat('L1/', $countrycode, '/', $l1)"/>
                <xsl:variable name="l2id" select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                <xsl:variable name="l3id" select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                <xsl:variable name="l4id" select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                <xsl:variable name="l5id" select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>

                <xsl:choose>
                    <xsl:when test="$l5!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l5id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l4!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l4id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l3!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l3id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l0!=''">
                        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Location">

        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="Name">
            <xsl:choose>
                <xsl:when test="$Building!=''">
                    <xsl:value-of select="$Building"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="col[@field='Name']/text()"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="l0">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Country"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="addr_postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>
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
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                           <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <xsl:variable name="l1id" select="concat('L1/', $countrycode, '/', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>

        <!-- Specific Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Location:', $Name, '/', $addr_street, '/', $lat, '/', $lon)"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l5!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l5id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l4id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l3id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l2id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l1id"/>
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
            <data field="name"><xsl:value-of select="$Name"/></data>
            <xsl:if test="$addr_street!=''">
                <data field="addr_street"><xsl:value-of select="$addr_street"/></data>
            </xsl:if>
            <xsl:if test="$addr_postcode!=''">
                <data field="addr_postcode"><xsl:value-of select="$addr_postcode"/></data>
            </xsl:if>
            <xsl:if test="$lat!=''">
                <data field="lat"><xsl:value-of select="$lat"/></data>
            </xsl:if>
            <xsl:if test="$lon!=''">
                <data field="lon"><xsl:value-of select="$lon"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
