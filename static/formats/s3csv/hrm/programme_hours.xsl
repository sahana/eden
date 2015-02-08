<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Programme Hours - CSV Import Stylesheet

         CSV fields:
         Organisation....................hrm_programme.owned_by_entity
         Programme.......................hrm_programme.name
         Job Title.......................hrm_programme.job_title_id$name
         First Name......................pr_person.first_name
         Last Name.......................pr_person.last_name
         Email...........................pr_contact (to deduplicate person)
         Mobile Phone....................pr_contact (to deduplicate person)
         Date............................hrm_programme_hours.date
         Hours...........................hrm_programme_hours.hours

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="orgs" match="row"
             use="col[@field='Organisation']"/>

    <xsl:key name="programmes" match="row"
             use="concat(col[@field='Organisation'],
                         col[@field='Programme'])"/>

    <xsl:key name="jobtitles" match="row"
             use="concat(col[@field='Organisation'],
                         col[@field='Job Title'])"/>

    <xsl:key name="persons" match="row"
             use="concat(col[@field='First Name'],
                         col[@field='Last Name'],
                         col[@field='Email'],
                         col[@field='Mobile Phone'])"/>
    
    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Programmes -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('programmes',
                                                        concat(col[@field='Organisation'],
                                                               col[@field='Programme']))[1])]">
                <xsl:call-template name="Programme"/>
            </xsl:for-each>

            <!-- Job Titles -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('jobtitles',
                                                        concat(col[@field='Organisation'],
                                                               col[@field='Job Title']))[1])]">
                <xsl:call-template name="JobTitle"/>
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('persons',
                                                        concat(col[@field='First Name'],
                                                               col[@field='Last Name'],
                                                               col[@field='Email'],
                                                               col[@field='Mobile Phone']))[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Programme Hours -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Organisation" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Programme" select="col[@field='Programme']/text()"/>
        <xsl:variable name="JobTitle" select="col[@field='Job Title']/text()"/>

        <resource name="hrm_programme_hours">
            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat(col[@field='First Name'],
                                                 col[@field='Last Name'],
                                                 col[@field='Email'],
                                                 col[@field='Mobile Phone'])"/>
                </xsl:attribute>
            </reference>
            <reference field="programme_id" resource="hrm_programme">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($Organisation,$Programme)"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="$JobTitle!=''">
                <reference field="job_title_id" resource="hrm_job_title">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($Organisation,$JobTitle)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            
            <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            <data field="hours"><xsl:value-of select="col[@field='Hours']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="Organisation" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Organisation"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Organisation"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Programme">
        <xsl:variable name="Organisation" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Programme" select="col[@field='Programme']/text()"/>

        <resource name="hrm_programme">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($Organisation,$Programme)"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$Programme"/></data>

            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Organisation"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="JobTitle">
        <xsl:variable name="Organisation" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="JobTitle" select="col[@field='Job Title']/text()"/>

        <resource name="hrm_job_title">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($Organisation,$JobTitle)"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$JobTitle"/></data>

            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Organisation"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="FirstName" select="col[@field='First Name']/text()"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']/text()"/>
        <xsl:variable name="Email" select="col[@field='Email']/text()"/>
        <xsl:variable name="MobilePhone" select="col[@field='Mobile Phone']/text()"/>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($FirstName,
                                             $LastName,
                                             $Email,
                                             $MobilePhone)"/>
            </xsl:attribute>

            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
            <data field="last_name"><xsl:value-of select="$LastName"/></data>

            <xsl:if test="$Email!=''">
                <resource name="pr_contact">
                    <data field="contact_method" value="EMAIL"/>
                    <data field="value">
                            <xsl:value-of select="$Email"/>
                    </data>
                </resource>
            </xsl:if>

            <xsl:if test="$MobilePhone!=''">
                <resource name="pr_contact">
                    <data field="contact_method" value="SMS"/>
                    <data field="value">
                        <xsl:value-of select="$MobilePhone"/>
                    </data>
                </resource>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
