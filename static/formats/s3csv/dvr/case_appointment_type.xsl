<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Case Appointment Type - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Type Name
         Active...............string..........is active
                                              true|false
         Comments.............string..........Comments

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
        <resource name="dvr_case_appointment_type">
            <data field="name">
                <xsl:value-of select="col[@field='Name']"/>
            </data>
            <xsl:variable name="is_active" select="col[@field='Active']/text()"/>
            <data field="is_active">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_active='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>
            <data field="comments">
                <xsl:value-of select="col[@field='Comments']"/>
            </data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
