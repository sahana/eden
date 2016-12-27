<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Case Status - CSV Import Stylesheet

         CSV column...........Format..........Content

         Position.............integer.........Workflow Position
         Code.................string..........Status Code
         Status...............string..........Status Name
         Default..............string..........is default status
                                              true|false
         Closed...............string..........cases with this status are closed
                                              true|false
         Not Transferable.....string..........cases with this status are not transferable
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
        <resource name="dvr_case_status">
            <data field="workflow_position">
                <xsl:value-of select="col[@field='Position']"/>
            </data>
            <data field="code">
                <xsl:value-of select="col[@field='Code']"/>
            </data>
            <data field="name">
                <xsl:value-of select="col[@field='Status']"/>
            </data>
            <xsl:variable name="is_default" select="col[@field='Default']/text()"/>
            <data field="is_default">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_default='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>
            <xsl:variable name="is_closed" select="col[@field='Closed']/text()"/>
            <data field="is_closed">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_closed='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>
            <xsl:variable name="is_not_transferable" select="col[@field='Not Transferable']/text()"/>
            <data field="is_not_transferable">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_not_transferable='true'">
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
