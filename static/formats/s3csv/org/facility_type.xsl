<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Facility Types - CSV Import Stylesheet

         CSV column...........Format..........Content

         Type...................string..........Facility Type Name
         SubType................string..........Facility Type Name @ToDo
         Volunteer Deployments..boolean.........Type Designates Sites for
                                                Volunteer Deployment (true|false)
         Comments...............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="org_facility_type">

            <data field="name"><xsl:value-of select="col[@field='Type']"/></data>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <xsl:variable name="vol_deployments" select="col[@field='Volunteer Deployments']/text()"/>
            <data field="vol_deployments">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$vol_deployments='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
