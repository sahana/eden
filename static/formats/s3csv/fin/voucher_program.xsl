<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Fin Product - CSV Import Stylesheet

         CSV column...........Format..........Content

         Organisation.........string..........Organisation Name
         Name.................string..........Name
         Description..........string..........Description
         Issuers..............string..........Organisation Group Name
         Providers............string..........Organisation Group Name
         Unit.................string..........Service Unit
         Price Per Unit.......float...........Price per Service Unit
         Currency.............string..........Currency for Unit Price
         Instructions.........text............Instructions to Voucher Bearers

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="projects" match="row" use="col[@field='Project']"/>
    <xsl:key name="issuers" match="row" use="col[@field='Issuers']"/>
    <xsl:key name="providers" match="row" use="col[@field='Providers']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Orgs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projects', col[@field='Project'])[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <!-- Issuers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('issuers', col[@field='Issuers'])[1])]">
                <xsl:call-template name="OrgGroup">
                    <xsl:with-param name="name">
                        <xsl:value-of select="col[@field='Issuers']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Providers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('providers', col[@field='Providers'])[1])]">
                <xsl:variable name="name" select="col[@field='Providers']"/>
                <xsl:if test="not(//col[@field='Issuers']/text()=$name)">
                    <xsl:call-template name="OrgGroup">
                        <xsl:with-param name="name" select="$name"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:for-each>

            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="fin_voucher_program">

            <!-- Basic Details -->
            <data field="name">
                <xsl:value-of select="col[@field='Name']/text()"/>
            </data>
            <data field="description">
                <xsl:value-of select="col[@field='Description']/text()"/>
            </data>

            <!-- Service Unit and Price Details -->
            <data field="unit">
                <xsl:value-of select="col[@field='Unit']/text()"/>
            </data>
            <data field="price_per_unit">
                <xsl:value-of select="col[@field='Price Per Unit']/text()"/>
            </data>
            <data field="currency">
                <xsl:value-of select="col[@field='Currency']/text()"/>
            </data>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']/text()"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Project -->
            <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
            <xsl:if test="$ProjectName!=''">
                <reference field="project_id" resource="project_project">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ProjectName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Issuers -->
            <xsl:variable name="issuers" select="col[@field='Issuers']/text()"/>
            <xsl:if test="$issuers!=''">
                <reference field="issuers_id" resource="org_group">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$issuers"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Providers -->
            <xsl:variable name="providers" select="col[@field='Providers']/text()"/>
            <xsl:if test="$providers!=''">
                <reference field="providers_id" resource="org_group">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$providers"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Instructions -->
            <xsl:variable name="instructions" select="col[@field='Instructions']/text()"/>
            <xsl:if test="$instructions!=''">
                <data field="voucher_instructions">
                    <xsl:value-of select="$instructions"/>
                </data>
            </xsl:if>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrganisationName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrganisationName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$ProjectName!=''">
            <resource name="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ProjectName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ProjectName"/></data>
                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrganisationName"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrgGroup">

        <xsl:param name="name"/>

        <xsl:if test="$name!=''">
            <resource name="org_group">
                <xsl:attribute name="tuid"><xsl:value-of select="$name"/></xsl:attribute>
                <data field="name"><xsl:value-of select="$name"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>

