<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Programme Hours - CSV Import Stylesheet

         CSV fields:
         Organisation....................hrm_programme.owned_by_entity
         Programme.......................hrm_programme.name
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
    <xsl:key name="orgs"
             match="row"
             use="col[@field='Organisation']"/>

    <xsl:key name="programmes"
             match="row"
             use="concat(col[@field='Organisation'],
                         col[@field='Programme'])"/>

    <xsl:key name="persons"
             match="row"
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
                    <xsl:value-of select="concat(col[@field='Organisation'],
                                                 col[@field='Programme'])"/>
                </xsl:attribute>
            </reference>
            
            <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            <data field="hours"><xsl:value-of select="col[@field='Hours']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="col[@field='Organisation']"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Organisation']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Programme">

        <resource name="hrm_programme">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat(col[@field='Organisation'],
                                             col[@field='Programme'])"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="col[@field='Programme']"/></data>

            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat(col[@field='First Name'],
                                             col[@field='Last Name'],
                                             col[@field='Email'],
                                             col[@field='Mobile Phone'])"/>
            </xsl:attribute>

            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>

            <xsl:if test="col[@field='Email']!=''">
                <resource name="pr_contact">
                    <data field="contact_method" value="EMAIL"/>
                    <data field="value">
                            <xsl:value-of select="col[@field='Email']/text()"/>
                    </data>
                </resource>
            </xsl:if>

            <xsl:if test="col[@field='Mobile Phone']!=''">
                <resource name="pr_contact">
                    <data field="contact_method" value="SMS"/>
                    <data field="value">
                        <xsl:value-of select="col[@field='Mobile Phone']/text()"/>
                    </data>
                </resource>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
