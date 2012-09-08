<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Users - CSV Import Stylesheet

         CSV fields:
         First Name..............auth_user.first_name
         Last Name...............auth_user.last_name
         Email...................auth_user.email
         Password................auth_user.password
         Role....................auth_group.role
         Organisation............org_organisation.name (Doesn't work as not a real Reference)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:key name="organisations" match="row" use="col[@field='Organisation']/text()"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('organisations',
                                                        col[@field='Organisation']/text())[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <!-- Create the User -->
        <resource name="auth_user">
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            <data field="email"><xsl:value-of select="col[@field='Email']"/></data>
            <data field="password">
                <xsl:attribute name="value">
                    <xsl:value-of select="col[@field='Password']"/>
                </xsl:attribute>
            </data>

            <!-- Every user must have the authenticated role -->
            <resource name="auth_membership">
                <reference field="group_id" resource="auth_group" uuid="AUTHENTICATED"/>
            </resource>

            <!-- Add other roles as per list -->
            <xsl:variable name="roles" select="col[@field='Role']/text()"/>
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$roles"/>
            </xsl:call-template>

            <!-- Link to Organisation -->
            <xsl:if test="$OrgName!=''">
                <data field="organisation_id">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
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
            <xsl:if test="$realm='0'">
                <data field="pe_id" value="0"/>
            </xsl:if>
            <xsl:if test="contains($realm, '=')">
                <data field="pe_id"><xsl:value-of select="$realm"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$OrgName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
