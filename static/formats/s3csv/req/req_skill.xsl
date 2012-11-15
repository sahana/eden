<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Request Skills - CSV Import Stylesheet

         CSV fields:
         Request........................req_req_item.req_id & req_req.req_ref (lookup only)
         Skill..........................req_req_item.skill_id & hrm_skill.name (lookup only)
         Quantity.......................req_req_item.quantity
         Comments.......................req_req_item.comments

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="request" match="row" use="col[@field='Request']"/>
    <xsl:key name="skill" match="row" use="col[@field='Skill']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Requests -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('request',
                                                                       col[@field='Request'])[1])]">
                <xsl:call-template name="Request" />
            </xsl:for-each>

            <!-- Skills -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('skill',
                                                                       col[@field='Skill'])[1])]">
                <xsl:call-template name="Skill" />
            </xsl:for-each>

            <!-- Req Items -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Skill" select="col[@field='Skill']"/>

        <!-- Request Skill -->
        <resource name="req_req_skill">
            <reference field="req_id" resource="req_req">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Request:', col[@field='Request'])"/>
                </xsl:attribute>
            </reference>
            <reference field="skill_id" resource="hrm_skill">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('[&quot;', 'Skill:', $Skill, '&quot;]')"/>
                </xsl:attribute>
            </reference>
            <data field="quantity"><xsl:value-of select="col[@field='Quantity']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Request">

        <xsl:variable name="Request" select="col[@field='Request']"/>

        <resource name="req_req">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Request:', $Request)"/>
            </xsl:attribute>
            <data field="req_ref"><xsl:value-of select="$Request"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Skill">

        <xsl:variable name="Skill" select="col[@field='Skill']"/>

        <resource name="hrm_skill">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Skill:', $Skill)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Skill"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
