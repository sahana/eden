<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Payment Service - CSV Import Stylesheet
         
         CSV column...........Format..........Content

         Organisation.........string..........Organisation Name
         Name.................string..........Name
         URL..................string..........Base URL
         Username.............string..........Username (Client ID)
         Password.............string..........Password (Client Secret)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="org" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Orgs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('org',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="fin_payment_service">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="base_url"><xsl:value-of select="col[@field='URL']"/></data>
            <data field="username"><xsl:value-of select="col[@field='Username']"/></data>
            <data field="password"><xsl:value-of select="col[@field='Password']"/></data>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="org" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$org"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$org"/></data>
       </resource>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
