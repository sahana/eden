<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Event Assets - CSV Import Stylesheet
         - useful for Demos/Simulations

         CSV column...........Format..........Content

         Incident.............string..........Incident Name
         Asset................string..........Asset Number
         Status...............string..........Status
         Budget...............string..........Budget Name
         Start................date............Start Date
         End..................date............End Date
         OneTimeCost..........number..........One-time cost
         DailyCost............number..........Daily cost

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="IncidentPrefix" select="'Incident:'"/>
    <xsl:variable name="AssetPrefix" select="'Asset:'"/>
    <xsl:variable name="BudgetPrefix" select="'Budget:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="incident" match="row" use="col[@field='Incident']"/>
    <xsl:key name="asset" match="row" use="col[@field='Asset']"/>
    <xsl:key name="budget" match="row" use="col[@field='Budget']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Incidents -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('incident',
                                                                   col[@field='Incident'])[1])]">
                <xsl:call-template name="Incident" />
            </xsl:for-each>

            <!-- Assets -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('asset',
                                                                   col[@field='Asset'])[1])]">
                <xsl:call-template name="Asset" />
            </xsl:for-each>

            <!-- Budgets -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('budget',
                                                                   col[@field='Budget'])[1])]">
                <xsl:call-template name="Budget" />
            </xsl:for-each>

            <!-- Links -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        <xsl:variable name="Incident" select="col[@field='Incident']"/>
        <xsl:variable name="Asset" select="col[@field='Asset']"/>
        <xsl:variable name="Budget" select="col[@field='Budget']/text()"/>
        
        <xsl:variable name="Status">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Status']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="event_asset">

            <!-- Link to Incident -->
            <reference field="incident_id" resource="event_incident">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($IncidentPrefix, $Incident)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Asset -->
            <reference field="asset_id" resource="asset_asset">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($AssetPrefix, $Asset)"/>
                </xsl:attribute>
            </reference>

            <xsl:choose>
                <xsl:when test="$Status=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Status='ALERTED'">
                    <data field="status">1</data>
                </xsl:when>
                <xsl:when test="$Status='STANDING BY'">
                    <data field="status">2</data>
                </xsl:when>
                <xsl:when test="$Status='ACTIVE'">
                    <data field="status">3</data>
                </xsl:when>
                <xsl:when test="$Status='DEACTIVATED'">
                    <data field="status">4</data>
                </xsl:when>
                <xsl:when test="$Status='UNABLE'">
                    <data field="status">5</data>
                </xsl:when>
            </xsl:choose>
            
            <!-- Budget allocation -->
            <xsl:if test="$Budget!=''">
                <resource name="budget_allocation">
                    <reference field="budget_id" resource="budget_budget">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($BudgetPrefix, $Budget)"/>
                        </xsl:attribute>
                    </reference>
                    <data field="unit_cost">
                        <xsl:value-of select="col[@field='OneTimeCost']/text()"/>
                    </data>
                    <data field="daily_cost">
                        <xsl:value-of select="col[@field='DailyCost']/text()"/>
                    </data>
                    <data field="start_date">
                        <xsl:value-of select="col[@field='Start']/text()"/>
                    </data>
                    <data field="end_date">
                        <xsl:value-of select="col[@field='End']/text()"/>
                    </data>
                </resource>
            </xsl:if>
            
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Incident">

        <xsl:variable name="IncidentName" select="col[@field='Incident']/text()"/>

        <xsl:if test="$IncidentName!=''">
            <resource name="event_incident">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($IncidentPrefix, $IncidentName)"/>
                </xsl:attribute>

                <data field="name"><xsl:value-of select="$IncidentName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Asset">

        <xsl:variable name="AssetName" select="col[@field='Asset']/text()"/>

        <xsl:if test="$AssetName!=''">
            <resource name="asset_asset">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($AssetPrefix, $AssetName)"/>
                </xsl:attribute>

                <data field="number"><xsl:value-of select="$AssetName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Budget">

        <xsl:variable name="Budget" select="col[@field='Budget']/text()"/>

        <resource name="budget_budget">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($BudgetPrefix, $Budget)"/>
            </xsl:attribute>
            <data field="name">
                <xsl:value-of select="$Budget"/>
            </data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
