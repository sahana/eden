<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
    
        <resource name="disease_disease">
            <data field="name">
                <xsl:value-of select="col[@field='Name']/text()"/>
            </data>

            <xsl:variable name="ShortName" select="col[@field='Short Name']/text()"/>
            <xsl:if test="$ShortName!=''">
                <data field="short_name">
                    <xsl:value-of select="$ShortName"/>
                </data>
            </xsl:if>

            <xsl:variable name="Acronym" select="col[@field='Acronym']/text()"/>
            <xsl:if test="$Acronym!=''">
                <data field="acronym">
                    <xsl:value-of select="$Acronym"/>
                </data>
            </xsl:if>

            <xsl:variable name="ICD10" select="col[@field='ICD10']/text()"/>
            <xsl:if test="$ICD10!=''">
                <data field="code">
                    <xsl:value-of select="$ICD10"/>
                </data>
            </xsl:if>
            
            <xsl:variable name="Description" select="col[@field='Description']/text()"/>
            <xsl:if test="$Description!=''">
                <data field="description">
                    <xsl:value-of select="$Description"/>
                </data>
            </xsl:if>
                
            <xsl:variable name="TracePeriod" select="col[@field='Trace Period']/text()"/>
            <xsl:if test="$TracePeriod!=''">
                <data field="trace_period">
                    <xsl:value-of select="$TracePeriod"/>
                </data>
            </xsl:if>
            
            <xsl:variable name="WatchPeriod" select="col[@field='Watch Period']/text()"/>
            <xsl:if test="$WatchPeriod!=''">
                <data field="watch_period">
                    <xsl:value-of select="$WatchPeriod"/>
                </data>
            </xsl:if>

            <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
            <xsl:if test="$Comments!=''">
                <data field="comments">
                    <xsl:value-of select="$Comments"/>
                </data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
