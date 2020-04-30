<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Facility - CSV Import Stylesheet

         CSV fields:
         Code....................org_facility.code
         Name....................org_facility.name
         Name L10n:XX............org_site_name.name_10n (Language = XX in column name, name_10n = cell in row. Multiple allowed)
         Type....................org_facility.facility_type_id (can be comma-sep list) or org_facility_type.parent
         SubType.................org_facility.facility_type_id (can be comma-sep list. Use ; between different parents) or org_facility_type.parent
         SubSubType..............org_facility.facility_type_id
         Organisation............org_organisation.name
         Organisation Group......org_site_org_group.group_id
         Main Facility...........org_facility.main_facility
                                 true|false (also accepts yes|no)
         Building................gis_location.name
         Address.................gis_location.addr_street
         Postcode................gis_location.addr_postcode
         Country.................gis_location.L0 Name or ISO2
         L1......................gis_location.L1
         L2......................gis_location.L2
         L3......................gis_location.L3
         L4......................gis_location.L4
         Lat.....................gis_location.lat
         Lon.....................gis_location.lon
         Contact.................org_facility.contact
         Phone...................org_facility.phone1
         Phone2..................org_facility.phone2
         Email...................org_facility.email
         Website.................org_facility.website
         Opening Times...........org_facility.opening_times
         Obsolete................org_facility.obsolete
         Comments................org_facility.comments
         Supplies Needed.........req_site_needs.goods_details
         Volunteers Needed.......req_site_needs.vol_details
         KV:XX...................Key,Value (Key = XX in column name, value = cell in row)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="FacilityTypePrefix" select="'FacilityType:'"/>
    <xsl:variable name="LocationPrefix" select="'Location:'"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Organisation">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Organisation</xsl:with-param>
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
    <xsl:key name="organisation" match="row" use="col[contains(
                    document('../labels.xml')/labels/column[@name='Organisation']/match/text(),
                    concat('|', @field, '|'))]"/>

    <xsl:key name="organisation_group" match="row" use="col[@field='Organisation Group']"/>

    <xsl:key name="type" match="row" use="concat(col[@field='Type'], '/',
                                                 col[@field='SubType'], '/',
                                                 col[@field='SubSubType'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('organisation',
                                            col[contains(
                                                document('../labels.xml')/labels/column[@name='Organisation']/match/text(),
                                                concat('|', @field, '|'))]
                                        )[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Organisation Group -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation_group',
                                                                       col[@field='Organisation Group'])[1])]">
                <xsl:call-template name="OrganisationGroup"/>
            </xsl:for-each>

            <!-- Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type',
                                                                   concat(col[@field='Type'], '/',
                                                                          col[@field='SubType'], '/',
                                                                          col[@field='SubSubType']))[1])]">
                <xsl:call-template name="splitMultiList">
                    <xsl:with-param name="arg">facility_type_res</xsl:with-param>
                    <xsl:with-param name="list"><xsl:value-of select="col[@field='Type']"/></xsl:with-param>
                    <xsl:with-param name="list2"><xsl:value-of select="col[@field='SubType']"/></xsl:with-param>
                    <xsl:with-param name="list3"><xsl:value-of select="col[@field='SubSubType']"/></xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the variables -->
        <xsl:variable name="FacilityName" select="col[@field='Name']/text()"/>
        <xsl:variable name="OrgName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Organisation"/>
            </xsl:call-template>
        </xsl:variable>

        <resource name="org_facility">

            <!-- Link to Location -->
            <reference field="location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($LocationPrefix, $FacilityName)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Organisation -->
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Org:', $OrgName)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Main Facility? -->
            <xsl:variable name="MainFacility" select="col[@field='Main Facility']/text()"/>
            <xsl:choose>
                <xsl:when test="$MainFacility='true' or $MainFacility='yes'">
                    <data field="main_facility" value="true"/>
                </xsl:when>
                <xsl:when test="$MainFacility='false' or $MainFacility='no'">
                    <data field="main_facility" value="false"/>
                </xsl:when>
            </xsl:choose>

            <!-- Link to Facility Type(s) -->
            <xsl:call-template name="splitMultiList">
                <xsl:with-param name="arg">facility_type_ref</xsl:with-param>
                <xsl:with-param name="list"><xsl:value-of select="col[@field='Type']"/></xsl:with-param>
                <xsl:with-param name="list2"><xsl:value-of select="col[@field='SubType']"/></xsl:with-param>
                <xsl:with-param name="list3"><xsl:value-of select="col[@field='SubSubType']"/></xsl:with-param>
            </xsl:call-template>

            <!-- Organisation Group -->
            <xsl:if test="col[@field='Organisation Group']!=''">
                <resource name="org_site_org_group">
                    <reference field="group_id" resource="org_group">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('OrganisationGroup:',
                                                         col[@field='Organisation Group'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- Site Needs (include if any of the columns exists) -->
            <xsl:if test="col[@field='Supplies Needed'] or col[@field='Volunteers Needed']">

               <resource name="req_site_needs">

                    <!-- Volunteers -->
                    <xsl:variable name="Volunteers" select="col[@field='Volunteers Needed']/text()"/>
                    <data field="vol">
                        <xsl:choose>
                            <xsl:when test="$Volunteers!=''">True</xsl:when>
                            <xsl:otherwise>False</xsl:otherwise>
                        </xsl:choose>
                    </data>
                    <data field="vol_details">
                        <xsl:value-of select="$Volunteers"/>
                    </data>

                    <!-- Supplies -->
                    <xsl:variable name="Supplies" select="col[@field='Supplies Needed']/text()"/>
                    <data field="goods">
                        <xsl:choose>
                            <xsl:when test="$Supplies!=''">True</xsl:when>
                            <xsl:otherwise>False</xsl:otherwise>
                        </xsl:choose>
                    </data>
                    <data field="goods_details">
                        <xsl:value-of select="$Supplies"/>
                    </data>

                </resource>
            </xsl:if>

            <!-- Facility data -->
            <!-- Facility Name field is max length 64 -->
            <data field="name"><xsl:value-of select="substring($FacilityName,1,64)"/></data>
            <xsl:if test="col[@field='Code']!=''">
                <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Opening Times']!=''">
                <data field="opening_times"><xsl:value-of select="col[@field='Opening Times']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Phone']!=''">
                <data field="phone1"><xsl:value-of select="col[@field='Phone']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Phone2']!=''">
                <data field="phone2"><xsl:value-of select="col[@field='Phone2']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Email']!=''">
                <data field="email"><xsl:value-of select="col[@field='Email']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Website']!=''">
                <data field="website"><xsl:value-of select="col[@field='Website']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Obsolete']!=''">
                <data field="obsolete"><xsl:value-of select="col[@field='Obsolete']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
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

        <xsl:call-template name="Locations"/>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="arg"/>
        <xsl:param name="item"/>
        <xsl:param name="item2" />
        <xsl:param name="item3" />

        <xsl:choose>
            <!-- Facility Types -->
            <!-- @todo: migrate to Taxonomy-pattern, see vulnerability/data.xsl -->
            <xsl:when test="$arg='facility_type_ref'">
                <resource name="org_site_facility_type">
                    <reference field="facility_type_id" resource="org_facility_type">
                        <xsl:attribute name="tuid">
                            <xsl:choose>
                                <xsl:when test="$item3!=''">
                                    <xsl:value-of select="concat($FacilityTypePrefix, $item, '/', $item2, '/', $item3)"/>
                                </xsl:when>
                                <xsl:when test="$item2!=''">
                                    <xsl:value-of select="concat($FacilityTypePrefix, $item, '/', $item2)"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="concat($FacilityTypePrefix, $item)"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='facility_type_res'">
                <resource name="org_facility_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($FacilityTypePrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
                <xsl:if test="$item2!=''">
                    <resource name="org_facility_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($FacilityTypePrefix, $item, '/', $item2)"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$item2"/></data>
                        <reference field="parent" resource="org_facility_type">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($FacilityTypePrefix, $item)"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
                <xsl:if test="$item3!=''">
                    <resource name="org_facility_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($FacilityTypePrefix, $item, '/', $item2, '/', $item3)"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$item3"/></data>
                        <reference field="parent" resource="org_facility_type">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($FacilityTypePrefix, $item, '/', $item2)"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:variable name="OrgName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Organisation"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$OrgName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Org:', $OrgName)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="FacilityType">
        <xsl:param name="Type"/>
        <xsl:param name="SubType"/>
        <xsl:param name="SubSubType"/>

        <xsl:choose>
            <xsl:when test="contains($Type, ',')">
                <!-- Comma-separated list -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list"><xsl:value-of select="$Type"/></xsl:with-param>
                    <xsl:with-param name="arg">facility_type_res</xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <resource name="org_facility_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($FacilityTypePrefix, $Type)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$Type"/></data>
                </resource>
                <xsl:if test="$SubType!=''">
                    <resource name="org_facility_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($FacilityTypePrefix, $Type, '/', $SubType)"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$SubType"/></data>
                        <reference field="parent" resource="org_facility_type">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($FacilityTypePrefix, $Type)"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
                <xsl:if test="$SubSubType!=''">
                    <resource name="org_facility_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($FacilityTypePrefix, $Type, '/', $SubType, '/', $SubSubType)"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$SubSubType"/></data>
                        <reference field="parent" resource="org_facility_type">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($FacilityTypePrefix, $Type, '/', $SubType)"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>

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
    <xsl:template name="OrganisationGroup">

        <xsl:variable name="OrganisationGroup" select="col[@field='Organisation Group']"/>

        <xsl:if test="$OrganisationGroup!=''">
            <resource name="org_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('OrganisationGroup:',
                                                 $OrganisationGroup)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrganisationGroup"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="FacilityName" select="col[@field='Name']/text()"/>
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
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

        <xsl:variable name="country"
                      select="concat('urn:iso:std:iso:3166:-1:code:',
                                     $countrycode)"/>

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

        <!-- Facility Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($LocationPrefix, $FacilityName)"/>
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
            <xsl:choose>
                <xsl:when test="$Building!=''">
                    <data field="name"><xsl:value-of select="$Building"/></data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="name"><xsl:value-of select="$FacilityName"/></data>
                </xsl:otherwise>
            </xsl:choose>
            <data field="addr_street"><xsl:value-of select="col[@field='Address']"/></data>
            <data field="addr_postcode"><xsl:value-of select="$postcode"/></data>
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
