<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Activities (Communities) - CSV Import Stylesheet

         2011-12-15 / Dominic König <dominic[AT]aidiq[DOT]com>

         CSV column...........Format..........Content

         Name.................string..........Activity (Community) short description
         Project..............string..........Project Name
         Activities...........comma-sep list..List of Activity Types
         Country..............string..........Country code/name (L0)
         State................string..........State/Province name (L1)
         District.............string..........District name (L2)
         City.................string..........City name (L3)
         Lat..................float...........Latitude
         Lon..................float...........Longitude
         ContactPersonXXX.....comma-sep list..Contact Person (can be multiple columns)
                                              as "FirstName,LastName,Email,MobilePhone",
                                              where first name and email as well as the
                                              three commas are mandatory
         Comments.............string..........Comments
         Beneficiaries:XXX....integer.........Number of Beneficiaries of type XXX (multiple allowed)

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="ActivityTypePrefix" select="'ActivityType: '"/>

    <xsl:key name="projects" match="row" use="col[@field='Project']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projects',
                                                                   col[@field='Project'])[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Beneficiaries')]">
                <xsl:call-template name="BeneficiaryType"/>
            </xsl:for-each>

            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="Activity" select="col[@field='Name']/text()"/>

        <resource name="project_activity">
            <data field="name"><xsl:value-of select="$Activity"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            <!-- Link to Project -->
            <reference field="project_id" resource="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Project:', $ProjectName)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Location -->
            <xsl:call-template name="LocationReference"/>

            <xsl:variable name="ActivityTypeRef">
                <xsl:call-template name="quoteList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="col[@field='Activities']"/>
                    </xsl:with-param>
                    <xsl:with-param name="prefix">
                        <xsl:value-of select="$ActivityTypePrefix"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:if test="$ActivityTypeRef">
                <reference field="multi_activity_type_id" resource="project_activity_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('[', $ActivityTypeRef, ']')"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:call-template name="ContactPersonReference"/>

            <xsl:for-each select="col[starts-with(@field, 'Beneficiaries')]">
                <xsl:call-template name="Beneficiaries"/>
            </xsl:for-each>

        </resource>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list">
                <xsl:value-of select="col[@field='Activities']"/>
            </xsl:with-param>
        </xsl:call-template>

        <xsl:call-template name="ContactPerson"/>

        <!-- Locations -->
        <xsl:call-template name="Locations"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>

        <resource name="project_project">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Project:', $ProjectName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ProjectName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>

        <resource name="project_activity_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($ActivityTypePrefix, $item)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$item"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Beneficiaries">

        <xsl:variable name="BeneficiaryType" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="BeneficiaryNumber" select="text()"/>

        <xsl:if test="$BeneficiaryNumber!=''">
            <resource name="project_beneficiary">
                <reference field="parameter_id" resource="project_beneficiary_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('BNF:', $BeneficiaryType)"/>
                    </xsl:attribute>
                </reference>
                <data field="number"><xsl:value-of select="$BeneficiaryNumber"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="BeneficiaryType">
        <xsl:variable name="BeneficiaryType" select="normalize-space(substring-after(@field, ':'))"/>

        <resource name="project_beneficiary_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('BNF:', $BeneficiaryType)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$BeneficiaryType"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="Project" select="col[@field='Project']/text()"/>
        <xsl:variable name="Activity" select="col[@field='Name']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $Activity)"/>

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
                    <xsl:value-of select="$l1id"/>
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
                    <xsl:value-of select="$l2id"/>
                </xsl:attribute>
                <xsl:choose>
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
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L3 Location -->
        <xsl:if test="$l3!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l3id"/>
                </xsl:attribute>
                <xsl:choose>
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
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- Activity Location -->
        <xsl:if test="$Activity!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l4id"/>
                </xsl:attribute>
                <xsl:choose>
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
                <data field="name"><xsl:value-of select="concat($Project, ': ', $Activity)"/></data>
                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">

        <xsl:variable name="Activity" select="col[@field='Name']/text()"/>

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $Activity)"/>

        <xsl:choose>
            <xsl:when test="$Activity!=''">
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
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactPerson">

        <xsl:variable name="Activity" select="col[@field='Name']/text()"/>

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='State']/text()"/>
        <xsl:variable name="l2" select="col[@field='District']/text()"/>
        <xsl:variable name="l3" select="col[@field='City']/text()"/>

        <xsl:variable name="l4id" select="concat('Location L4: ', $Activity)"/>

        <xsl:for-each select="col[starts-with(@field, 'ContactPerson')]">
            <xsl:variable name="PersonData" select="text()"/>
            <xsl:variable name="FirstName" select="substring-before($PersonData, ',')"/>
            <xsl:variable name="LastName" select="substring-before(substring-after($PersonData, ','), ',')"/>
            <xsl:variable name="Email" select="substring-before(substring-after(substring-after($PersonData, ','), ','), ',')"/>
            <xsl:variable name="MobilePhone" select="substring-after(substring-after(substring-after($PersonData, ','), ','), ',')"/>

            <xsl:if test="$FirstName!='' and $Email!=''">
                <resource name="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Contact:', $Email)"/>
                    </xsl:attribute>
                    <data field="first_name"><xsl:value-of select="$FirstName"/></data>
                    <data field="last_name"><xsl:value-of select="$LastName"/></data>

                    <!-- Address -->
                    <resource name="pr_address">
                        <!-- Link to Location (fails inside here)
                        <xsl:call-template name="LocationReference"/> -->
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l4id"/>
                            </xsl:attribute>
                        </reference>

                        <!-- Home address -->
                        <data field="type">1</data>

                        <!-- Populate the fields directly which are normally populated onvalidation -->
                        <data field="address">
                            <xsl:value-of select="$Activity"/>
                        </data>
                        <data field="L0">
                            <xsl:value-of select="$l0"/>
                        </data>
                        <data field="L1">
                            <xsl:value-of select="$l1"/>
                        </data>
                        <data field="L2">
                            <xsl:value-of select="$l2"/>
                        </data>
                        <data field="L3">
                            <xsl:value-of select="$l3"/>
                        </data>
                    </resource>

                    <!-- Contacts -->
                    <resource name="pr_contact">
                        <data field="contact_method">EMAIL</data>
                        <data field="value"><xsl:value-of select="$Email"/></data>
                    </resource>
                    <xsl:if test="$MobilePhone!=''">
                        <resource name="pr_contact">
                            <data field="contact_method">SMS</data>
                            <data field="value"><xsl:value-of select="$MobilePhone"/></data>
                        </resource>
                    </xsl:if>
                </resource>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactPersonReference">

        <xsl:for-each select="col[starts-with(@field, 'ContactPerson')]">
            <xsl:variable name="PersonData" select="text()"/>
            <xsl:variable name="FirstName" select="substring-before($PersonData, ',')"/>
            <xsl:variable name="LastName" select="substring-before(substring-after($PersonData, ','), ',')"/>
            <xsl:variable name="Email" select="substring-before(substring-after(substring-after($PersonData, ','), ','), ',')"/>
            <xsl:variable name="MobilePhone" select="substring-after(substring-after(substring-after($PersonData, ','), ','), ',')"/>
            <xsl:if test="$FirstName!='' and $Email!=''">

                <resource name="project_activity_contact">
                    <reference field="person_id" resource="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Contact:', $Email)"/>
                        </xsl:attribute>
                    </reference>
                </resource>

            </xsl:if>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>

