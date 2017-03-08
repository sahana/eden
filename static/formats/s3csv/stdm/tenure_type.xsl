<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Tenure Types - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Tenure Type Name
         Profile..............string..........Profile Name
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="ProfilePrefix" select="'Profile:'"/>

    <xsl:key name="profiles" match="row" use="col[@field='Profile']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Profiles -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('profiles',
                                                                   col[@field='Profile'])[1])]">
                <xsl:call-template name="Profile"/>
            </xsl:for-each>

            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="stdm_tenure_type">
            <xsl:variable name="Profile" select="col[@field='Profile']/text()"/>

            <!-- Link to Profile -->
            <xsl:if test="$Profile!=''">
                <reference field="profile_id" resource="stdm_profile">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($ProfilePrefix, $Profile)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Profile">
        <xsl:variable name="Profile" select="col[@field='Profile']/text()"/>

        <xsl:if test="$Profile!=''">
            <resource name="stdm_profile">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ProfilePrefix, $Profile)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Profile"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
