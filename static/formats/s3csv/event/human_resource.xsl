<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Event Human Resources - CSV Import Stylesheet
         - useful for Demos/Simulations

         CSV column...........Format..........Content

         Incident.............string..........Incident Name
         Organisation.........string..........Organisation Name
         First Name...........string..........First Name
         Last Name............string..........Last Name
         Status...............string..........Status
         Budget...............string..........Budget Name
         Start................date............Start Date
         End..................date............End Date
         OneTimeCost..........number..........One-time cost
         DailyCost............number..........Daily cost

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="BudgetPrefix" select="'Budget:'"/>
    <xsl:variable name="IncidentPrefix" select="'Incident:'"/>
    <xsl:variable name="HumanResourcePrefix" select="'Human Resource:'"/>
    <xsl:variable name="OrgPrefix" select="'Organisation:'"/>
    <xsl:variable name="PersonPrefix" select="'Person:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="budget" match="row" use="col[@field='Budget']"/>
    <xsl:key name="incident" match="row" use="col[@field='Incident']"/>
    <xsl:key name="org" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="person" match="row" use="concat(col[@field='Organisation'],
                                                   col[@field='First Name'],
                                                   col[@field='Last Name'])"/>
    <xsl:key name="hr" match="row" use="concat(col[@field='Organisation'],
                                               col[@field='First Name'],
                                               col[@field='Last Name'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Budgets -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('budget',
                                                                   col[@field='Budget'])[1])]">
                <xsl:call-template name="Budget" />
            </xsl:for-each>

            <!-- Incidents -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('incident',
                                                                       col[@field='Incident'])[1])]">
                <xsl:call-template name="Incident" />
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('org',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation" />
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('person',
                                                                       concat(col[@field='Organisation'],
                                                                              col[@field='First Name'],
                                                                              col[@field='Last Name']))[1])]">
                <xsl:call-template name="Person" />
            </xsl:for-each>

            <!-- Human Resources -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('hr',
                                                                       concat(col[@field='Organisation'],
                                                                              col[@field='First Name'],
                                                                              col[@field='Last Name']))[1])]">
                <xsl:call-template name="HumanResource" />
            </xsl:for-each>

            <!-- Links -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        <xsl:variable name="Budget" select="col[@field='Budget']/text()"/>
        <xsl:variable name="Incident" select="col[@field='Incident']/text()"/>
        <xsl:variable name="HumanResource">
            <xsl:value-of select="concat(col[@field='Organisation'],
                                         col[@field='First Name'],
                                         col[@field='Last Name'])"/>
        </xsl:variable>
        <xsl:variable name="Status">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Status']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="event_human_resource">

            <!-- Link to Incident -->
            <reference field="incident_id" resource="event_incident">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($IncidentPrefix, $Incident)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Human Resource -->
            <reference field="human_resource_id" resource="hrm_human_resource">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($HumanResourcePrefix, $HumanResource)"/>
                </xsl:attribute>
            </reference>

            <!-- Status -->
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
    <xsl:template name="Organisation">

        <xsl:variable name="OrgName" select="col[@field='Organisation']"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($OrgPrefix, $OrgName)"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">

        <xsl:variable name="PersonName" select="concat(col[@field='First Name'],
                                                       col[@field='Last Name'])"/>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($PersonPrefix, $PersonName)"/>
            </xsl:attribute>

            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="HumanResource">
        <xsl:variable name="PersonName" select="concat(col[@field='First Name'],
                                                       col[@field='Last Name'])"/>
        <xsl:variable name="HumanResource">
            <xsl:value-of select="concat(col[@field='Organisation'],
                                         col[@field='First Name'],
                                         col[@field='Last Name'])"/>
        </xsl:variable>

        <resource name="hrm_human_resource">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($HumanResourcePrefix, $HumanResource)"/>
            </xsl:attribute>

            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($OrgPrefix, col[@field='Organisation'])"/>
                </xsl:attribute>
            </reference>

            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($PersonPrefix, $PersonName)"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->


</xsl:stylesheet>
