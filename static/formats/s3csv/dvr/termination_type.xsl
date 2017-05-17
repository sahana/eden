<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Case Activity Termination Types - CSV Import Stylesheet

         CSV column...........Format..........Content

         Service..............string..........Service Type Name
         Termination Type.....string..........Termination Type Name
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Service Index -->
    <xsl:key name="services" match="row" use="col[@field='Service']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Services from Index -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('services',
                                                                       col[@field='Service'])[1])]">
                <xsl:call-template name="Service"/>
            </xsl:for-each>

            <!-- Termination Types -->
            <xsl:apply-templates select="./table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="dvr_termination_type">

            <!-- Link to service -->
            <xsl:variable name="Service" select="col[@field='Service']/text()"/>
            <xsl:if test="$Service!=''">
                <reference field="service_id" resource="org_service">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('SERVICE:', $Service)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Termination Type Name and Comments -->
            <data field="name">
                <xsl:value-of select="col[@field='Termination Type']"/>
            </data>
            <data field="comments">
                <xsl:value-of select="col[@field='Comments']"/>
            </data>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Service">

        <xsl:variable name="Service" select="col[@field='Service']/text()"/>
        <xsl:if test="$Service!=''">

            <resource name="org_service">

                <!-- TUID -->
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('SERVICE:', $Service)"/>
                </xsl:attribute>

                <!-- Service Name -->
                <data field="name">
                    <xsl:value-of select="$Service"/>
                </data>

            </resource>

        </xsl:if>
    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>
