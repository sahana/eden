<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Event Human Resources - CSV Import Stylesheet
         - useful for Demos/Simulations

         CSV column...........Format..........Content

         Incident.............string..........Incident Name
         First Name...........string..........First Name
         Last Name............string..........Last Name
         Status...............string..........Status

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../commons.xsl"/>

    <xsl:variable name="IncidentPrefix" select="'Incident:'"/>
    <xsl:variable name="HumanResourcePrefix" select="'Human Resource:'"/>
    <xsl:variable name="PersonPrefix" select="'Person:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="incident" match="row" use="col[@field='Incident']"/>
    <xsl:key name="person" match="row" use="concat(col[@field='First Name'],
                                                   col[@field='Last Name'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Incidents -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('incident',
                                                                   col[@field='Incident'])[1])]">
                <xsl:call-template name="Incident" />
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('person',
                                                                   concat(col[@field='First Name'],
                                                                          col[@field='Last Name']))[1])]">
                <xsl:call-template name="Person" />
            </xsl:for-each>

            <!-- Human Resources -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('person',
                                                                   concat(col[@field='First Name'],
                                                                          col[@field='Last Name']))[1])]">
                <xsl:call-template name="HumanResource" />
            </xsl:for-each>

            <!-- Links -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        <xsl:variable name="Incident">
            <xsl:value-of select="col[@field='Incident']"/>
        </xsl:variable>
        <xsl:variable name="HumanResource">
            <xsl:value-of select="concat(col[@field='First Name'],
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
    <xsl:template name="Person">

        <xsl:variable name="PersonName" select="col[@field='Incident']/text()"/>

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
        <xsl:variable name="HumanResource">
            <xsl:value-of select="concat(col[@field='First Name'],
                                         col[@field='Last Name'])"/>
        </xsl:variable>

        <resource name="hrm_human_resource">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($HumanResourcePrefix, $HumanResource)"/>
            </xsl:attribute>

            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($PersonPrefix, $HumanResource)"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
