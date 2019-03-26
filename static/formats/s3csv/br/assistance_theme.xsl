<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         BR Assistance Themes - CSV Import Stylesheet

         CSV column..................Format..........Content

         Organisation................string..........Organisation Name
         Branch.........................optional.....Organisation Branch Name
         ...SubBranch,SubSubBranch...etc (indefinite depth, must specify all from root)

         Sector......................string..........Sector Name
         Need........................string..........Need Type Name
         Generic Need................string..........need type is not org-specific
                                                     true|false (default false)
         Theme.......................string..........Theme Name
         Comments....................string..........Comments

    *********************************************************************** -->

    <xsl:import href="../orgh.xsl"/>

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="sectors" match="row" use="col[@field='Sector']"/>
    <xsl:key name="needs" match="row" use="col[@field='Need']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>

            <!-- Import the organisation hierarchy -->
            <xsl:for-each select="table/row[1]">
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="level">Organisation</xsl:with-param>
                    <xsl:with-param name="rows" select="//table/row"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Sectors -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('sectors',
                                                                   col[@field='Sector'])[1])]">
                <xsl:call-template name="Sector"/>
            </xsl:for-each>

            <!-- Needs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('needs',
                                                                   col[@field='Need'])[1])]">
                <xsl:call-template name="Need"/>
            </xsl:for-each>

            <!-- Process all rows for response themes -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Response Themes -->
    <xsl:template match="row">

        <xsl:variable name="Name" select="col[@field='Theme']"/>
        <xsl:if test="$Name!=''">

            <resource name="br_assistance_theme">

                <!-- Name -->
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>

                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>

                <!-- Link to sector -->
                <xsl:variable name="Sector" select="col[@field='Sector']/text()"/>
                <xsl:if test="$Sector!=''">
                    <reference field="sector_id" resource="org_sector">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('SECTOR:', $Sector)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Link to need -->
                <xsl:variable name="Need" select="col[@field='Need']/text()"/>
                <xsl:if test="$Need!=''">
                    <reference field="need_id" resource="br_need">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('NEED:', $Need)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Comments -->
                <data field="comments">
                    <xsl:value-of select="col[@field='comments']"/>
                </data>

            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Sectors -->
    <xsl:template name="Sector">

        <xsl:variable name="Name" select="col[@field='Sector']/text()"/>
        <xsl:if test="$Name!=''">
            <resource name="org_sector">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('SECTOR:', $Name)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Needs -->
    <xsl:template name="Need">

        <xsl:variable name="Name" select="col[@field='Need']/text()"/>
        <xsl:if test="$Name!=''">
            <resource name="br_need">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('NEED:', $Name)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>
                <!-- Link to Organisation if not generic -->
                <xsl:if test="not(col[@field='Generic Need']/text()='true')">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:call-template name="OrganisationID"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>
