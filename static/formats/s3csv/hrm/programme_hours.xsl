<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Programme Hours - CSV Import Stylesheet

         CSV fields:
         Organisation....................hrm_programme.owned_by_entity
         Branch..........................hrm_human_resource.organisation_id
         Programme.......................hrm_programme.name
         Job Title.......................hrm_programme.job_title_id$name
         First Name......................pr_person.first_name
         Middle Name.....................pr_person.middle_name
         Last Name.......................pr_person.last_name
         Email...........................pr_contact (to deduplicate person)
         Mobile Phone....................pr_contact (to deduplicate person)
         National ID.....................pr_identity (to deduplicate person)
         Organisation ID.................hrm_human_resource.code (to deduplicate person)
         Date............................hrm_programme_hours.date
         Hours...........................hrm_programme_hours.hours

    *********************************************************************** -->
    <xsl:import href="person.xsl"/>
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="MiddleName">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">MiddleName</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="LastName">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">LastName</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="root_orgs" match="row"
             use="col[@field='Organisation']"/>

    <xsl:key name="programmes" match="row"
             use="concat(col[@field='Organisation'],
                         col[@field='Programme'])"/>

    <xsl:key name="jobtitles" match="row"
             use="concat(col[@field='Organisation'],
                         col[@field='Job Title'])"/>

    <xsl:key name="persons" match="row"
             use="concat(col[@field='First Name'],
                         col[contains(document('../labels.xml')/labels/column[@name='MiddleName']/match/text(),
                             concat('|', @field, '|'))],
                         col[contains(document('../labels.xml')/labels/column[@name='LastName']/match/text(),
                             concat('|', @field, '|'))],
                         col[@field='Email'],
                         col[@field='Mobile Phone'],
                         col[@field='National ID'],
                         col[@field='Organisation ID'])"/>
    
    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Import the Organisation hierarchy -->
            <xsl:for-each select="table/row[1]">
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="level">Organisation</xsl:with-param>
                    <xsl:with-param name="rows" select="//table/row"/>
                </xsl:call-template>
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
                                                               col[contains(document('../labels.xml')/labels/column[@name='MiddleName']/match/text(),
                                                                   concat('|', @field, '|'))],
                                                               col[contains(document('../labels.xml')/labels/column[@name='LastName']/match/text(),
                                                                   concat('|', @field, '|'))],
                                                               col[@field='Email'],
                                                               col[@field='Mobile Phone'],
                                                               col[@field='National ID'],
                                                               col[@field='Organisation ID']))[1])]">
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
                                                 col[contains(document('../labels.xml')/labels/column[@name='MiddleName']/match/text(),
                                                     concat('|', @field, '|'))],
                                                 col[contains(document('../labels.xml')/labels/column[@name='LastName']/match/text(),
                                                     concat('|', @field, '|'))],
                                                 col[@field='Email'],
                                                 col[@field='Mobile Phone'],
                                                 col[@field='National ID'],
                                                 col[@field='Organisation ID'])"/>
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
                    <xsl:value-of select="concat('ORG:', $Organisation)"/>
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
                    <xsl:value-of select="concat('ORG:', $Organisation)"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="FirstName" select="col[@field='First Name']/text()"/>
        <xsl:variable name="MiddleName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$MiddleName"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="LastName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$LastName"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Email" select="col[@field='Email']/text()"/>
        <xsl:variable name="MobilePhone" select="col[@field='Mobile Phone']/text()"/>
        <xsl:variable name="NationalID" select="col[@field='National ID']/text()"/>
        <xsl:variable name="OrganisationID" select="col[@field='Organisation ID']/text()"/>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($FirstName,
                                             $MiddleName,
                                             $LastName,
                                             $Email,
                                             $MobilePhone,
                                             $NationalID,
                                             $OrganisationID)"/>
            </xsl:attribute>

            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
            <data field="middle_name"><xsl:value-of select="$MiddleName"/></data>
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

            <xsl:if test="$NationalID!=''">
                <resource name="pr_identity">
                    <data field="type" value="2"/>
                    <data field="value">
                        <xsl:value-of select="$NationalID"/>
                    </data>
                </resource>
            </xsl:if>

            <xsl:if test="$OrganisationID!=''">
                <resource name="hrm_human_resource">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:call-template name="OrganisationID"/>
                        </xsl:attribute>
                    </reference>
                    <data field="type">
                        <!-- Volunteer -->
                        <xsl:value-of select="2"/>
                    </data>
                    <data field="code">
                        <xsl:value-of select="$OrganisationID"/>
                    </data>
                </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
