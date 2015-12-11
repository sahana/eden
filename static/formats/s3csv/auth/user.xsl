<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Users - CSV Import Stylesheet

         CSV fields:
         First Name..............auth_user.first_name
         Last Name...............auth_user.last_name (Can also call the column Middle Name to allow Hispanic names to be used across both hrm/person & auth_user)
         Email...................auth_user.email
         Password................auth_user.password
         Language................auth_user.language
         Role....................auth_group.role
         Organisation............org_organisation.name
         Branch..................branch organisation name (only 1 level supported. If need a SubBranch then put Branch in Organisation column & SubBranch in Branch column)
         Organisation Group......org_group.name

         @ToDo: Add support for Sites to auth.s3_import_prep
         - meanwhile, can add these via hrm/person.xsl
         Facility Type...........s3db[tablename]
         Office..................org_site.name

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:key name="groups" match="row" use="col[@field='Organisation Group']/text()"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisation Groups -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('groups',
                                                        col[@field='Organisation Group']/text())[1])]">
                <xsl:call-template name="OrganisationGroup"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
        <xsl:variable name="GroupName" select="col[@field='Organisation Group']/text()"/>

        <!-- Create the User -->
        <resource name="auth_user">
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <xsl:choose>
                <xsl:when test="col[@field='Last Name']!=''">
                    <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
                </xsl:when>
                <xsl:when test="col[@field='Middle Name']!=''">
                    <data field="last_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
                </xsl:when>
            </xsl:choose>
            <data field="email"><xsl:value-of select="col[@field='Email']"/></data>
            <data field="password">
                <xsl:attribute name="value">
                    <xsl:value-of select="col[@field='Password']"/>
                </xsl:attribute>
            </data>
            <xsl:if test="col[@field='Language']!=''">
                <data field="language"><xsl:value-of select="col[@field='Language']"/></data>
            </xsl:if>

            <!-- Add other roles as per list -->
            <xsl:variable name="roles" select="col[@field='Role']/text()"/>
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$roles"/>
            </xsl:call-template>

            <!-- Link to Organisation -->
            <xsl:choose>
                <xsl:when test="$BranchName!=''">
                    <!-- Link to the Branch -->
                    <data field="organisation_id">
                        <!-- Name gets converted to ID in auth.s3_import_prep -->
                        <xsl:value-of select="concat($OrgName, '+BRANCH+', $BranchName)"/>
                    </data>
                </xsl:when>
                <xsl:when test="$OrgName!=''">
                    <!-- Link to the top-level Organisation -->
                    <data field="organisation_id">
                        <!-- Name gets converted to ID in auth.s3_import_prep -->
                        <xsl:value-of select="$OrgName"/>
                    </data>
                </xsl:when>
            </xsl:choose>

            <!-- Link to Organisation Group -->
            <xsl:if test="$GroupName!=''">
                <data field="org_group_id">
                    <!-- Name gets converted to ID in auth.s3_import_prep -->
                    <xsl:value-of select="$GroupName"/>
                </data>
            </xsl:if>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>

        <xsl:variable name="role">
            <xsl:choose>
                <xsl:when test="contains($item, '/')">
                    <xsl:value-of select="substring-before($item, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$item"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="realm">
            <xsl:choose>
                <xsl:when test="contains($item, '/')">
                    <xsl:value-of select="substring-after($item, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'default'"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource name="auth_membership">
            <reference field="group_id" resource="auth_group">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$role"/>
                </xsl:attribute>
            </reference>
            <xsl:choose>
                <xsl:when test="$realm='0'">
                    <data field="pe_id" value="0"/>
                </xsl:when>
                <!-- e.g. org_organisation.name=Viet Nam Red Cross -->
                <xsl:when test="contains($realm, '=')">
                    <data field="pe_id"><xsl:value-of select="$realm"/></data>
                </xsl:when>
            </xsl:choose>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrganisationGroup">
        <xsl:variable name="GroupName" select="col[@field='Organisation Group']/text()"/>

        <xsl:if test="$GroupName!=''">
            <resource name="org_group">
                <data field="name"><xsl:value-of select="$GroupName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
