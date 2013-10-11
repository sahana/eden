<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Regions - CSV Import Stylesheet

         CSV column...........Format..........Content

         Parent...............string..........Region Parent
         Name.................string..........Region Name
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../commons.xsl"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="region" match="row" use="col[@field='Parent']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Parent Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('region',
                                                                       col[@field='Parent'])[1])]">
                <xsl:call-template name="Region" />
            </xsl:for-each>

            <!-- Regions -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        <resource name="org_region">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            <xsl:if test="col[@field='Parent']!=''">
                <reference field="parent" resource="org_region">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Parent']"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Region">
        <xsl:if test="col[@field='Parent']!=''">
            <resource name="org_region">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Parent']"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="col[@field='Parent']"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
