<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Programmes - CSV Import Stylesheet

         CSV fields:
         Name............................hrm_programme.name
         Long Name.......................hrm_programme.name_long
         Description.....................hrm_programme.comments
         Organisation....................hrm_programme.owned_by_entity

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="orgs"
             match="row"
             use="col[@field='Organisation']"/>

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
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="hrm_programme">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="name_long"><xsl:value-of select="col[@field='Long Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Description']"/></data>
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
