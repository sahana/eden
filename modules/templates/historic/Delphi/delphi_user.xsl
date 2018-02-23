<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Users - CSV Import Stylesheet

         Fran

         CSV fields:
         First Name..............auth_user
         Last Name...............auth_user
         Email...................auth_user
         Password................auth_user
         Role....................auth_role
         DelphiGroup.............delphi_membership

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:key name="groups" match="row" use="col[@field='DelphiGroup']/text()"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Delphi Groups -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('groups',
                                                        col[@field='DelphiGroup']/text())[1])]">
                <xsl:call-template name="DelphiGroup"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="DelphiGroup" select="col[@field='DelphiGroup']/text()"/>
        <xsl:variable name="Email" select="col[@field='Email']/text()"/>

        <!-- Create the User -->
        <resource name="auth_user">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Email"/>
            </xsl:attribute>
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            <data field="email"><xsl:value-of select="$Email"/></data>
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

        </resource>
        
        <xsl:if test="$DelphiGroup!=''">
            <resource name="delphi_membership">
                <reference field="group_id" resource="delphi_group">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$DelphiGroup"/>
                    </xsl:attribute>
                </data>
                <reference field="user_id" resource="auth_user">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Email"/>
                    </xsl:attribute>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>

        <resource name="auth_membership">
            <reference field="group_id" resource="auth_group">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$item"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="DelphiGroup">
        <xsl:variable name="DelphiGroup" select="col[@field='DelphiGroup']/text()"/>

        <xsl:if test="$DelphiGroup!=''">
            <resource name="delphi_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$DelphiGroup"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$DelphiGroup"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
