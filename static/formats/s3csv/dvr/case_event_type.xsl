<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Case Event Type - CSV Import Stylesheet

         CSV column..................Format..........Content

         Code........................string..........Type Code
         Name........................string..........Type Name
         Default.....................string..........is default type
                                                     true|false
         Minimum Interval............number..........minimum interval (hours)
         Presence required...........string..........requires personal presence
                                                     true|false
         Comments....................string..........Comments

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

        <xsl:variable name="Code" select="col[@field='Code']/text()"/>
        <xsl:variable name="Name" select="col[@field='Name']/text()"/>

        <resource name="dvr_case_event_type">

            <data field="code">
                <xsl:value-of select="$Code"/>
            </data>

            <data field="name">
                <xsl:value-of select="$Name"/>
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

            <xsl:variable name="MinimumInterval" select="col[@field='Minimum Interval']/text()"/>
            <xsl:if test="$MinimumInterval!=''">
                <data field="min_interval">
                    <xsl:value-of select="$MinimumInterval"/>
                </data>
            </xsl:if>

            <!-- Requires personal presence -->

            <xsl:variable name="presence_required" select="col[@field='Presence required']/text()"/>
            <data field="presence_required">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$presence_required='false'">
                            <xsl:value-of select="'false'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'true'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <data field="comments">
                <xsl:value-of select="col[@field='Comments']/text()"/>
            </data>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
