<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Shelter Registrations - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Shelter........................required.....Shelter Name
         Unit...........................required.....Shelter Unit Name
         First Name.....................required.....Person First Name
         Middle Name....................optional.....Person Middle Name
         Last Name......................optional.....Person Last Name
         Comments.......................optional.....Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:param name="mode"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="shelter" match="row" use="col[@field='Shelter']"/>
    <xsl:key name="shelter_unit" match="row" use="col[@field='Unit']"/>

    <xsl:key name="person" match="row"
             use="concat(col[@field='First Name'], '/',
                         col[@field='Last Name'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Shelters -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('shelter', col[@field='Shelter'])[1])]">
                <xsl:call-template name="Shelter"/>
            </xsl:for-each>

            <!-- Shelter Units -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('shelter_unit', col[@field='Unit'])[1])]">
                <xsl:call-template name="ShelterUnit"/>
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('person',
                                                        concat(col[@field='First Name'], '/',
                                                               col[@field='Last Name']))[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Process all table rows for shelter unit records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Shelter Registration Record -->
    <xsl:template match="row">
        <xsl:variable name="ShelterName" select="col[@field='Shelter']/text()"/>
        <xsl:variable name="ShelterUnitName" select="col[@field='Unit']/text()"/>
        <xsl:variable name="FirstName" select="col[@field='First Name']/text()"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']/text()"/>

        <resource name="cr_shelter_registration">

            <reference field="shelter_id" resource="cr_shelter">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ShelterName"/>
                </xsl:attribute>
            </reference>

            <reference field="shelter_unit_id" resource="cr_shelter_unit">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ShelterName,$ShelterUnitName)"/>
                </xsl:attribute>
            </reference>

            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Person:', $LastName, ',', $FirstName)"/>
                </xsl:attribute>
            </reference>

            <data field="registration_status">
                <!-- Planned -->
                <xsl:text>1</xsl:text>
            </data>

            <!-- Comments -->
            <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
            <xsl:if test="$Comments!=''">
                <data field="comments">
                    <xsl:value-of select="$Comments"/>
                </data>
            </xsl:if>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Shelter">
        <xsl:variable name="shelter" select="col[@field='Shelter']/text()"/>

        <resource name="cr_shelter">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$shelter"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$shelter"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ShelterUnit">
        <xsl:variable name="ShelterName" select="col[@field='Shelter']/text()"/>
        <xsl:variable name="ShelterUnitName" select="col[@field='Unit']/text()"/>

        <xsl:if test="$ShelterName!='' and $ShelterUnitName!=''">
            <resource name="cr_shelter_unit">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ShelterName,$ShelterUnitName)"/>
                </xsl:attribute>

                <data field="name">
                    <xsl:value-of select="$ShelterUnitName"/>
                </data>

                <reference field="shelter_id" resource="cr_shelter">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ShelterName"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="FirstName" select="col[@field='First Name']/text()"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']/text()"/>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Person:', $LastName, ',', $FirstName)"/>
            </xsl:attribute>
            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
            <data field="last_name"><xsl:value-of select="$LastName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
