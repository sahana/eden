<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Request Approvers - CSV Import Stylesheet

         CSV fields:
         Entity............................req_approver.pe_id$name
         Entity Type.......................req_approver.pe_id$instance_type
         Title.............................req_approver.title
         First Name........................req_approver.person_id$first_name
         Middle Name.......................req_approver.person_id$middle_name
         Last Name.........................req_approver.person_id$last_name
         Matcher...........................req_approver.matcher

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="entity" match="row"
             use="concat(col[@field='Entity'],col[@field='Entity Type'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Entities -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('entity',
                                                                       concat(col[@field='Entity'],
                                                                              col[@field='Entity Type']))[1])]">
                <xsl:call-template name="Entity"/>
            </xsl:for-each>

            <!-- Approvers -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="EntityType"><xsl:value-of select="col[@field='Entity Type']"/></xsl:variable>
        <xsl:variable name="Matcher">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Matcher']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="req_approver">
            <reference field="pe_id">
                <xsl:attribute name="resource">
                    <xsl:value-of select="$EntityType"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($EntityType, col[@field='Entity'])"/>
                </xsl:attribute>
            </reference>
            <data field="title"><xsl:value-of select="col[@field='Title']"/></data>
            <reference field="person_id" resource="pr_person">
                <resource name="pr_person">
                    <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
                    <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
                    <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
                </resource>
            </reference>
            <xsl:choose>
                <xsl:when test="$Matcher=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Matcher='Y'">
                    <data field="matcher" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Matcher='YES'">
                    <data field="matcher" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Matcher='T'">
                    <data field="matcher" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Matcher='TRUE'">
                    <data field="matcher" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Matcher='N'">
                    <data field="matcher" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Matcher='NO'">
                    <data field="matcher" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Matcher='F'">
                    <data field="matcher" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Matcher='FALSE'">
                    <data field="matcher" value="false">False</data>
                </xsl:when>
            </xsl:choose>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Entity">
        <xsl:variable name="Entity"><xsl:value-of select="col[@field='Entity']"/></xsl:variable>
        <xsl:variable name="EntityType"><xsl:value-of select="col[@field='Entity Type']"/></xsl:variable>

        <resource>
            <xsl:attribute name="name">
                <xsl:value-of select="$EntityType"/>
            </xsl:attribute>
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($EntityType, $Entity)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Entity"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
