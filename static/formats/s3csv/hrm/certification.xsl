<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Certificates - CSV Import Stylesheet

         CSV fields:
         First Name......................pr_person.first_name
         Middle Name.....................pr_person.middle_name
         Last Name.......................pr_person.last_name
         Email...........................pr_contact.value
         Mobile Phone....................pr_contact.value
         Certificate.....................hrm_certificate.name
         Organisation....................hrm_certificate.organisation
         License Number..................hrm_certification.number
         Expiry Date.....................hrm_certification.date
         Comments........................hrm_certification.comments

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="orgs" match="row" use="col[@field='Organisation']"/>

    <xsl:key name="certs" match="row" use="col[@field='Certificate']"/>

    <xsl:key name="person" match="row"
             use="concat(col[@field='First Name'], '/',
                         col[@field='Middle Name'], '/',
                         col[@field='Last Name'], '/',
                         col[@field='Email'], '/',
                         col[@field='Mobile Phone'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('orgs', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Certs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('certs', col[@field='Certificate'])[1])]">
                <xsl:call-template name="Certificate"/>
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

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="CertName" select="col[@field='Certificate']"/>
        <xsl:variable name="Number" select="col[@field='License Number']"/>
        <xsl:variable name="Date" select="col[@field='Expiry Date']"/>
        <xsl:variable name="FirstName" select="col[@field='First Name']"/>
        <xsl:variable name="MiddleName" select="col[@field='Middle Name']"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']"/>
        <xsl:variable name="Email" select="col[@field='Email']"/>
        <xsl:variable name="Mobile" select="col[@field='Mobile Phone']"/>

        <!-- HRM Certification -->
        <resource name="hrm_certification">
            <reference field="certificate_id" resource="hrm_certificate">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Cert:', $CertName)"/>
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
            <xsl:if test="$Number!=''">
                <data field="number"><xsl:value-of select="$Number"/></data>
            </xsl:if>
            <xsl:if test="$Date!=''">
                <data field="date"><xsl:value-of select="$Date"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Certificate">
        <xsl:variable name="CertName" select="col[@field='Certificate']"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']"/>

        <resource name="hrm_certificate">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Cert:', $CertName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CertName"/></data>
            <xsl:if test="$OrgName!=''">
                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
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

</xsl:stylesheet>
