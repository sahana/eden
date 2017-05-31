<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Case Event Type - CSV Import Stylesheet

         CSV column..................Format..........Content

         Code........................string..........Type Code
         Name........................string..........Type Name
         Inactive....................string..........is currently not selectable
                                                     true|false
         Default.....................string..........is default type
                                                     true|false
         Minimum Interval............number..........minimum interval (hours)
         Maximum per Day.............integer.........maximum number per day
         Excluded By.................string..........comma-separated list of event
                                                     type codes that exclude the
                                                     registration of this event type
                                                     for the same person on the same
                                                     day (NB this will not remove
                                                     any existing exclusion rules)
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

            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('TYPE:', $Code)"/>
            </xsl:attribute>

            <data field="code">
                <xsl:value-of select="$Code"/>
            </data>

            <data field="name">
                <xsl:value-of select="$Name"/>
            </data>

            <xsl:variable name="is_inactive" select="col[@field='Inactive']/text()"/>
            <xsl:if test="$is_inactive!=''">
                <data field="is_inactive">
                    <xsl:attribute name="value">
                        <xsl:choose>
                            <xsl:when test="$is_inactive='true'">
                                <xsl:value-of select="'true'"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'false'"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </data>
            </xsl:if>

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

            <!-- Minimum time interval between occurences -->
            <xsl:variable name="MinimumInterval" select="col[@field='Minimum Interval']/text()"/>
            <xsl:if test="$MinimumInterval!=''">
                <data field="min_interval">
                    <xsl:value-of select="$MinimumInterval"/>
                </data>
            </xsl:if>

            <!-- Maximum number of occurences per day -->
            <xsl:variable name="MaxPerDay" select="col[@field='Maximum per Day']/text()"/>
            <xsl:if test="$MaxPerDay!=''">
                <data field="max_per_day">
                    <xsl:value-of select="$MaxPerDay"/>
                </data>
            </xsl:if>

            <!-- Exclusions through other event types -->
            <xsl:variable name="ExcludedBy" select="col[@field='Excluded By']/text()"/>
            <xsl:if test="$ExcludedBy!=''">
                <xsl:call-template name="Exclusions">
                    <xsl:with-param name="ExcludedBy" select="$ExcludedBy"/>
                </xsl:call-template>
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
    <xsl:template name="Exclusions">

        <xsl:param name="ExcludedBy"/>

        <xsl:choose>
            <xsl:when test="contains($ExcludedBy,',')">
                <xsl:variable name="head" select="normalize-space(substring-before($ExcludedBy, ','))"/>
                <xsl:call-template name="Exclusion">
                    <xsl:with-param name="Code" select="$head"/>
                </xsl:call-template>
                <xsl:call-template name="Exclusions">
                    <xsl:with-param name="ExcludedBy" select="substring-after($ExcludedBy, ',')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Exclusion">
                    <xsl:with-param name="Code" select="$ExcludedBy"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Exclusion">

        <xsl:param name="Code"/>

        <xsl:if test="//row[col[@field='Code']/text()=$Code]">
            <resource name="dvr_case_event_exclusion" alias="excluded_by">
                <reference field="excluded_by_id" resource="dvr_case_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('TYPE:', $Code)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
