<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
         DVR Case Appointments - CSV Import Stylesheet

         CSV column..................Format..........Content

         UUID........................urn:uuid........the person UUID
         ID..........................string..........the person PE-label
                                                     (ignored if UUID present)

         NB Either UUID or ID must identify an existing person
         record - no person record can be created with this import.

         Appointment Type............string..........the appointment type name,
                                                     mandatory
         Appointment Date............ISO date........the appointment date,
                                                     mandatory
         Appointment Status..........string..........the appointment status,
                                                     mandatory
                                                     Planning|Planned|In Progress|Completed|
                                                     Missed|Cancelled|Not Required
         Comments....................string..........comments for the appointment,
                                                     optional

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Index for Appointment Types -->
    <xsl:key name="types" match="row" use="col[@field='Appointment Type']/text()"/>

    <!-- Index for Person PE Labels -->
    <xsl:key name="persons" match="row" use="col[@field='ID']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Appointment types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('types', col[@field='Appointment Type']/text())[1])]">
                <xsl:call-template name="AppointmentType"/>
            </xsl:for-each>

            <!-- Persons by PE Label -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('persons', col[@field='ID']/text())[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="PersonUUID" select="col[@field='UUID']/text()"/>
        <xsl:variable name="PersonLabel" select="col[@field='ID']/text()"/>

        <xsl:variable name="Type" select="col[@field='Appointment Type']/text()"/>
        <xsl:variable name="Date" select="col[@field='Appointment Date']/text()"/>
        <xsl:variable name="Status" select="col[@field='Appointment Status']/text()"/>
        <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>

        <xsl:if test="($PersonUUID!='' or $PersonLabel!='') and $Type!='' and $Status!=''">

            <resource name="dvr_case_appointment">

                <!-- Link to person -->
                <xsl:choose>
                    <xsl:when test="$PersonUUID!=''">
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$PersonUUID"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$PersonLabel!=''">
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('PERSON:', $PersonLabel)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>

                <!-- Link to appointment type -->
                <reference field="type_id" resource="dvr_case_appointment_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('APPOINTMENT_TYPE:', $Type)"/>
                    </xsl:attribute>
                </reference>

                <!-- Date -->
                <data field="date">
                    <xsl:value-of select="$Date"/>
                </data>

                <!-- Status -->
                <data field="status">
                    <xsl:choose>
                        <xsl:when test="$Status='Planning'">1</xsl:when>
                        <xsl:when test="$Status='Planned'">2</xsl:when>
                        <xsl:when test="$Status='In Progress'">3</xsl:when>
                        <xsl:when test="$Status='Completed'">4</xsl:when>
                        <xsl:when test="$Status='Missed'">5</xsl:when>
                        <xsl:when test="$Status='Cancelled'">6</xsl:when>
                        <xsl:when test="$Status='Not Required'">7</xsl:when>
                        <xsl:when test="$Status!=''">
                            <!-- Use unparsed -->
                            <xsl:value-of select="$Status"/>
                        </xsl:when>
                        <xsl:otherwise>1</xsl:otherwise>
                    </xsl:choose>
                </data>

                <data field="comments">
                    <xsl:value-of select="$Comments"/>
                </data>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">

        <xsl:variable name="ID" select="col[@field='ID']/text()"/>

        <xsl:if test="$ID!=''">
            <resource name="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('PERSON:', $ID)"/>
                </xsl:attribute>
                <data field="pe_label">
                    <xsl:value-of select="$ID"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AppointmentType">

        <xsl:variable name="Type" select="col[@field='Appointment Type']/text()"/>
        <xsl:if test="$Type!=''">
            <resource name="dvr_case_appointment_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('APPOINTMENT_TYPE:', $Type)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$Type"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
