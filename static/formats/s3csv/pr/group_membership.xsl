<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Groups - CSV Import Stylesheet

         CSV fields:
         Group Name......................pr_group.name
         Group Type......................pr_group.group_type
         First Name......................pr_person.first_name
         Middle Name.....................pr_person.middle_name
         Last Name.......................pr_person.last_name
         Email...........................pr_contact.value
         Mobile Phone....................pr_contact.value

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="group" match="row"
             use="concat(col[@field='Group Type'], '/', col[@field='Group Name'])"/>

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
                                                                   concat(col[@field='Group Type'], '/', 
                                                                          col[@field='Group Name']))[1])]">
                <xsl:call-template name="Group"/>
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
        <xsl:variable name="GroupName" select="col[@field='Group Name']"/>
        <xsl:variable name="GroupType" select="col[@field='Group Type']"/>
        <xsl:variable name="FirstName" select="col[@field='First Name']"/>
        <xsl:variable name="MiddleName" select="col[@field='Middle Name']"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']"/>
        <xsl:variable name="Email" select="col[@field='Email']"/>
        <xsl:variable name="Mobile" select="col[@field='Mobile Phone']"/>

        <resource name="pr_group_membership">
            <reference field="group_id" resource="pr_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Group:', $GroupType, '/', $GroupName)"/>
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
        <xsl:variable name="GroupName" select="col[@field='Group Name']"/>
        <xsl:variable name="GroupType"><xsl:value-of select="col[@field='Group Type']"/></xsl:variable>

        <resource name="pr_group">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Group:', $GroupType, '/', $GroupName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$GroupName"/></data>
            <xsl:variable name="GROUPTYPE">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                       <xsl:value-of select="$GroupType"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="$GROUPTYPE='FAMILY'">
                    <data field="group_type">1</data>
                </xsl:when>
                <xsl:when test="$GROUPTYPE='TOURIST GROUP'">
                    <data field="group_type">2</data>
                </xsl:when>
                <xsl:when test="$GROUPTYPE='RELIEF TEAM'">
                    <data field="group_type">3</data>
                </xsl:when>
                <xsl:when test="$GROUPTYPE='MAILING LISTS'">
                    <data field="group_type">5</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Default to Relief team -->
                    <data field="group_type">3</data>
                </xsl:otherwise>
            </xsl:choose>
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

</xsl:stylesheet>
