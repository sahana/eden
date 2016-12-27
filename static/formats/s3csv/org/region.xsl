<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Regions - CSV Import Stylesheet

         CSV column...........Format..........Content

         Parent...............string..........Region Parent
         Region...............string..........Region Name
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="parent" match="row" use="col[@field='Parent']"/>
    <xsl:key name="region" match="row" use="concat(col[@field='Parent'],
                                                   col[@field='Region'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Parent Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('parent',
                                                                       col[@field='Parent'])[1])]">
                <xsl:call-template name="Region">
                    <xsl:with-param name="RegionName">
                        <xsl:value-of select="col[@field='Parent']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('region',
                                                                       concat(col[@field='Parent'],
                                                                              col[@field='Region']))[1])]">
                <xsl:call-template name="Region">
                    <xsl:with-param name="ParentName">
                        <xsl:value-of select="col[@field='Parent']"/>
                    </xsl:with-param>
                    <xsl:with-param name="RegionName">
                        <xsl:value-of select="col[@field='Region']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!--
            <xsl:apply-templates select="./table/row"/>
            -->
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Region">
        <xsl:param name="RegionName"/>
        <xsl:param name="ParentName"/>

        <xsl:if test="$RegionName!=''">
            <resource name="org_region">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$RegionName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$RegionName"/></data>
                <xsl:if test="$ParentName!=''">
                    <reference field="parent" resource="org_region">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ParentName"/>
                        </xsl:attribute>
                    </reference>
                    <xsl:if test="col[@field='Comments']!=''">
                        <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
                    </xsl:if>
                </xsl:if>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
