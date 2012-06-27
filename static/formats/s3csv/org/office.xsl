<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Office - CSV Import Stylesheet

         CSV fields:
         Name....................org_office
         Organisation............org_organisation
         Branch..................org_organisation[_branch]
         Type....................org_office
         Country.................org_office.L0 Name or ISO2
         Building................org_office.building_name
         Address.................org_office.address
         Postcode................org_office.postcode
         State...................org_office.L1
         District................org_office.L2
         City....................org_office.L3
         Lat.....................gis_location.lat
         Lon.....................gis_location.lon
         Phone1..................org_office
         Phone2..................org_office
         Email...................org_office
         Fax.....................org_office
         Comments................org_office

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- Office types, see modules/eden/org.py -->
    <org:office-type code="1">Headquarters</org:office-type>
    <org:office-type code="2">Regional</org:office-type>
    <org:office-type code="3">National</org:office-type>
    <org:office-type code="4">Field</org:office-type>
    <org:office-type code="5">Warehouse</org:office-type>

    <!-- Indexes for faster processing -->
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="branch" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
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

            <!-- Offices -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the variables -->
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
        <xsl:variable name="OfficeName" select="col[@field='Name']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

        <resource name="org_office">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OfficeName"/>
            </xsl:attribute>
            <!-- Link to Location -->
            <reference field="location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OfficeName"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:choose>
                        <xsl:when test="$BranchName!=''">
                            <xsl:value-of select="concat($OrgName,$BranchName)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$OrgName"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </reference>

            <xsl:variable name="typename" select="col[@field='Type']"/>
            <xsl:variable name="typecode" select="document('')//org:office-type[text()=normalize-space($typename)]/@code"/>
            <xsl:if test="$typecode">
                <data field="type"><xsl:value-of select="$typecode"/></data>
            </xsl:if>

            <!-- Office data -->
            <data field="name"><xsl:value-of select="$OfficeName"/></data>
            <data field="L0"><xsl:value-of select="$l0"/></data>
            <data field="L1"><xsl:value-of select="$l1"/></data>
            <data field="L2"><xsl:value-of select="$l2"/></data>
            <data field="L3"><xsl:value-of select="$l3"/></data>
            <data field="building_name"><xsl:value-of select="col[@field='Building']"/></data>
            <data field="address"><xsl:value-of select="col[@field='Address']"/></data>
            <data field="phone1"><xsl:value-of select="col[@field='Phone1']"/></data>
            <data field="phone2"><xsl:value-of select="col[@field='Phone2']"/></data>
            <data field="email"><xsl:value-of select="col[@field='Email']"/></data>
            <data field="postcode"><xsl:value-of select="col[@field='Postcode']"/></data>
            <data field="fax"><xsl:value-of select="col[@field='Fax']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

        <xsl:call-template name="Locations"/>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <!-- Create the Organisation/Branch -->
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
                <resource name="org_organisation_branch">
                    <reference field="organisation_id">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Organisation']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Locations">

        <xsl:variable name="OfficeName" select="col[@field='Name']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

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

        <!-- Office Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OfficeName"/>
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
            <data field="name"><xsl:value-of select="$OfficeName"/></data>
            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            <data field="addr_street">
                <xsl:value-of select="concat(col[@field='Address'], ', ',
                                             col[@field='City'], ', ',
                                             col[@field='State'])"/>
            </data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
