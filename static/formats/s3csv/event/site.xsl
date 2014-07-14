<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Event Sites - CSV Import Stylesheet
         - useful for Demos/Simulations

         CSV column...........Format..........Content

         Incident.............string..........Incident Name
         Facility.............string..........Facility Name
         Facility Type........string..........Facility Type
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
    <xsl:variable name="FacilityPrefix" select="'Facility:'"/>
    <xsl:variable name="BudgetPrefix" select="'Budget:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="incident" match="row" use="col[@field='Incident']"/>
    <xsl:key name="site" match="row" use="col[@field='Facility']"/>
    <xsl:key name="budget" match="row" use="col[@field='Budget']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Incidents -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('incident',
                                                                   col[@field='Incident'])[1])]">
                <xsl:call-template name="Incident" />
            </xsl:for-each>

            <!-- Sites -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('site',
                                                                   col[@field='Facility'])[1])]">
                <xsl:call-template name="Facility" />
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
        <xsl:variable name="Facility" select="col[@field='Facility']"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']"/>
        <xsl:variable name="Budget" select="col[@field='Budget']/text()"/>
        
        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        
        <xsl:variable name="Status">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Status']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="event_site">

            <!-- Link to Incident -->
            <reference field="incident_id" resource="event_incident">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($IncidentPrefix, $Incident)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Facility -->
            <reference field="site_id">
                <xsl:attribute name="resource">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($FacilityPrefix, $Facility)"/>
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
    <xsl:template name="Facility">

        <!--
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>-->
        <xsl:variable name="FacilityName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="$FacilityName!=''">
            <resource>
                <xsl:attribute name="name">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($FacilityPrefix, $FacilityName)"/>
                </xsl:attribute>

                <data field="name"><xsl:value-of select="$FacilityName"/></data>

                <!-- Link to Organisation
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:choose>
                            <xsl:when test="$BranchName!=''">
                                <xsl:value-of select="concat($OrgName,'/',$BranchName)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$OrgName"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </reference> -->
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
