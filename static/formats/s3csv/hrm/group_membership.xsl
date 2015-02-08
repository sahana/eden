<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Groups - CSV Import Stylesheet

         CSV fields:
         Team Name.......................pr_group.name
         First Name......................pr_person.first_name
         Middle Name.....................pr_person.middle_name
         Last Name.......................pr_person.last_name
         Email...........................pr_contact.value
         Mobile Phone....................pr_contact.value
         HR Type.........................hrm_human_resource.type
         Organisation....................hrm_human_resource.organisation_id
         Branch..........................hrm_human_resource.organisation_id

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="group" match="row"
             use="col[@field='Team Name']"/>

    <xsl:key name="orgs" match="row"
             use="col[@field='Organisation']"/>

    <xsl:key name="branches" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>

    <xsl:key name="person" match="row"
             use="concat(col[@field='First Name'], '/',
                         col[@field='Middle Name'], '/',
                         col[@field='Last Name'], '/',
                         col[@field='Email'], '/',
                         col[@field='Mobile Phone'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Groups -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('group',
                                                                   col[@field='Team Name'])[1])]">
                <xsl:call-template name="Group"/>
            </xsl:for-each>

            <!-- Top-level Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('orgs', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName"></xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Branches -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('branches', concat(col[@field='Organisation'], '/', col[@field='Branch']))[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName"></xsl:with-param>
                    <xsl:with-param name="BranchName">
                        <xsl:value-of select="col[@field='Branch']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('person',
                                                                   concat(col[@field='First Name'], '/',
                                                                          col[@field='Middle Name'], '/',
                                                                          col[@field='Last Name'], '/',
                                                                          col[@field='Email'], '/',
                                                                          col[@field='Mobile Phone']))[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Memberships -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="GroupName" select="col[@field='Team Name']"/>
        <xsl:variable name="FirstName" select="col[@field='First Name']"/>
        <xsl:variable name="MiddleName" select="col[@field='Middle Name']"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']"/>
        <xsl:variable name="Email" select="col[@field='Email']"/>
        <xsl:variable name="Mobile" select="col[@field='Mobile Phone']"/>

        <resource name="pr_group_membership">
            <reference field="group_id" resource="pr_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Group:', $GroupName)"/>
                </xsl:attribute>
            </reference>
            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Person:', $FirstName, '/',
                                                            $MiddleName, '/',
                                                            $LastName, '/',
                                                            $Email, '/',
                                                            $Mobile)"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Group">
        <xsl:variable name="GroupName" select="col[@field='Team Name']"/>

        <resource name="pr_group">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Group:', $GroupName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$GroupName"/></data>
            <!-- Default to Relief team -->
            <data field="group_type">3</data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="FirstName" select="col[@field='First Name']"/>
        <xsl:variable name="MiddleName" select="col[@field='Middle Name']"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']"/>
        <xsl:variable name="Email" select="col[@field='Email']"/>
        <xsl:variable name="Mobile" select="col[@field='Mobile Phone']"/>

        <resource name="pr_person">

            <!-- Person record -->
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Person:', $FirstName, '/',
                                                        $MiddleName, '/',
                                                        $LastName, '/',
                                                        $Email, '/',
                                                        $Mobile)"/>
            </xsl:attribute>
            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
            <data field="middle_name"><xsl:value-of select="$MiddleName"/></data>
            <data field="last_name"><xsl:value-of select="$LastName"/></data>
            
            <!-- Contact Information -->
            <xsl:if test="$Email!='' or $Mobile!=''">
                <xsl:call-template name="ContactInformation"/>
            </xsl:if>

            <!-- HR record -->
            <xsl:if test="col[@field='Organisation']!=''">
                <xsl:call-template name="HumanResource"/>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactInformation">
        <xsl:variable name="Email" select="col[@field='Email']"/>
        <xsl:variable name="Mobile" select="col[@field='Mobile Phone']"/>

        <xsl:if test="$Email!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="EMAIL"/>
                <data field="value">
                    <xsl:value-of select="$Email"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="$Mobile!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SMS"/>
                <data field="value">
                    <xsl:value-of select="$Mobile"/>
                </data>
            </resource>
        </xsl:if>

        <!--
        <xsl:if test="col[@field='Home Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="HOME_PHONE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Home Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Office Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="WORK_PHONE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Office Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Skype']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SKYPE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Skype']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Callsign']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="RADIO"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Callsign']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Emergency Contact Name']!=''">
            <resource name="pr_contact_emergency">
                <data field="name">
                    <xsl:value-of select="col[@field='Emergency Contact Name']/text()"/>
                </data>
                <data field="relationship">
                    <xsl:value-of select="col[@field='Emergency Contact Relationship']/text()"/>
                </data>
                <data field="phone">
                    <xsl:value-of select="col[@field='Emergency Contact Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>-->

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="HumanResource">
        <xsl:variable name="OrgName" select="col[@field='Organisation']"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']"/>
        <xsl:variable name="Type">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='HR Type']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="hrm_human_resource">

            <!-- HR data -->
            <xsl:choose>
                <xsl:when test="$Type='1'">
                    <data field="type">1</data>
                </xsl:when>
                <xsl:when test="$Type='S'">
                    <data field="type">1</data>
                </xsl:when>
                <xsl:when test="$Type='STAFF'">
                    <data field="type">1</data>
                </xsl:when>
                <xsl:when test="$Type='2'">
                    <data field="type">2</data>
                </xsl:when>
                <xsl:when test="$Type='V'">
                    <data field="type">2</data>
                </xsl:when>
                <xsl:when test="$Type='VOL'">
                    <data field="type">2</data>
                </xsl:when>
                <xsl:when test="$Type='VOULNTEER'">
                    <data field="type">2</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Default to Staff -->
                    <data field="type">1</data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:choose>
                        <xsl:when test="$BranchName!=''">
                            <xsl:value-of select="concat($OrgName,'/',$BranchName)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$OrgName"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <xsl:choose>
            <xsl:when test="$BranchName!=''">
                <!-- This is the Branch -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat(col[@field='Organisation'],'/',$BranchName)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$BranchName"/></data>
                    <!-- Don't create Orgs as Branches of themselves -->
                    <xsl:if test="col[@field='Organisation']!=$BranchName">
                        <resource name="org_organisation_branch" alias="parent">
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="col[@field='Organisation']"/>
                                </xsl:attribute>
                            </reference>
                        </resource>
                    </xsl:if>
                </resource>
            </xsl:when>
            <xsl:when test="$OrgName!=''">
                <!-- This is the top-level Organisation -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OrgName"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
