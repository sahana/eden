<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Requests - CSV Import Stylesheet

         CSV fields:
         Scenario.......................scenario_scenario.name (Optional)
         Event..........................event_event.name (Optional)
         Request Type...................req_req.type
         Template.......................req_req.is_template
         Request Number.................req_req.req_ref
         Date Requested.................req_req.date
         Priority.......................req_req.priority
         Purpose........................req_req.purpose
         Date Required..................req_req.date_required
         Requester......................req_req.requester_id (lookup only)
         Assigned To....................req_req.assigned_to_id (lookup only)
         Approved By....................req_req.approved_by_id (lookup only)
         Requested For..................req_req.request_for_id (lookup only)
         Requested for Facility.........req_req.site_id (lookup only)
         Requested for Facility Type....req_req.site_id (site type)
         Transportation Required........req_req.transport_req
         Security Required..............req_req.security_req
         Date Delivered.................req_req.date_recv
         Received By....................req_req.recv_by_id (lookup only)
         KV:XX..........................Key,Value (Key = XX in column name, value = cell in row)
         Comments.......................req_req.comments

         @ToDo: Templates

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="scenario" match="row" use="col[@field='Scenario']"/>
    <xsl:key name="event" match="row" use="col[@field='Event']"/>
    <xsl:key name="facility" match="row" use="col[@field='Requested for Facility']"/>
    <xsl:key name="requester_id" match="row" use="col[@field='Requester']"/>
    <xsl:key name="assigned_to_id" match="row" use="col[@field='Assigned To']"/>
    <xsl:key name="approved_by_id" match="row" use="col[@field='Approved By']"/>
    <xsl:key name="request_for_id" match="row" use="col[@field='Requested For']"/>
    <xsl:key name="recv_by_id" match="row" use="col[@field='Received By']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Scenarios -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('scenario',
                                                                       col[@field='Scenario'])[1])]">
                <xsl:call-template name="Scenario" />
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('event',
                                                                       col[@field='Event'])[1])]">
                <xsl:call-template name="Event" />
            </xsl:for-each>

            <!-- Facilities -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('facility',
                                                                       col[@field='Requested for Facility'])[1])]">
                <xsl:call-template name="Facility" />
            </xsl:for-each>

            <!-- Requesters -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('requester_id',
                                                                       col[@field='Requester'])[1])]">
                <xsl:call-template name="HumanResource">
                    <xsl:with-param name="Name">
                        <xsl:value-of select="col[@field='Requester']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Assignees -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('assigned_to_id',
                                                                       col[@field='Assigned To'])[1])]">
                <xsl:call-template name="HumanResource">
                    <xsl:with-param name="Name">
                        <xsl:value-of select="col[@field='Assigned To']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Approvers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('approved_by_id',
                                                                       col[@field='Approved By'])[1])]">
                <xsl:call-template name="HumanResource">
                    <xsl:with-param name="Name">
                        <xsl:value-of select="col[@field='Approved By']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Requested For -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('request_for_id',
                                                                       col[@field='Requested For'])[1])]">
                <xsl:call-template name="HumanResource">
                    <xsl:with-param name="Name">
                        <xsl:value-of select="col[@field='Requested For']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Receivers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('recv_by_id',
                                                                       col[@field='Received By'])[1])]">
                <xsl:call-template name="HumanResource">
                    <xsl:with-param name="Name">
                        <xsl:value-of select="col[@field='Received By']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Requests -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Event" select="col[@field='Event']"/>
        <xsl:variable name="Priority" select="col[@field='Priority']"/>
        <xsl:variable name="Type" select="col[@field='Request Type']"/>
        <xsl:variable name="FacilityName" select="col[@field='Requested for Facility']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Requested for Facility Type']/text()"/>

        <!-- Request -->
        <resource name="req_req">
            <xsl:if test="$Event!=''">
                <reference field="event_id" resource="event_event">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Event:', $Event)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$Type='Stock'">
                    <data field="type">1</data>
                </xsl:when>
                <xsl:when test="$Type='Items'">
                    <data field="type">1</data>
                </xsl:when>
                <xsl:when test="$Type='Asset'">
                    <data field="type">2</data>
                </xsl:when>
                <xsl:when test="$Type='People'">
                    <data field="type">3</data>
                </xsl:when>
                <!--
                <xsl:when test="$Type='Summary'">
                    <data field="type">8</data>
                </xsl:when>
                <xsl:when test="$Type='Other'">
                    <data field="type">9</data>
                </xsl:when>-->
                <xsl:otherwise>
                    <!-- other -->
                    <data field="type">9</data>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$Priority='Low'">
                    <data field="priority">1</data>
                </xsl:when>
                <xsl:when test="$Priority='Medium'">
                    <data field="priority">2</data>
                </xsl:when>
                <xsl:when test="$Priority='High'">
                    <data field="priority">3</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Medium -->
                    <data field="priority">2</data>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:variable name="resourcename">
                <xsl:choose>
                    <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                    <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                    <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                    <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                    <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                    <xsl:otherwise>inv_warehouse</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <reference field="site_id">
                <xsl:attribute name="resource">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Facility:', $FacilityName)"/>
                </xsl:attribute>
            </reference>
            <xsl:choose>
                <xsl:when test="col[@field='Template']='True'">
                    <data field="is_template">True</data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="is_template">False</data>
                    <data field="req_ref"><xsl:value-of select="col[@field='Request Number']"/></data>
                    <data field="date"><xsl:value-of select="col[@field='Date Requested']"/></data>
                    <data field="date_required"><xsl:value-of select="col[@field='Date Required']"/></data>
                    <data field="date_recv"><xsl:value-of select="col[@field='Date Delivered']"/></data>
                    <xsl:if test="col[@field='Approved By']!=''">
                        <reference field="approved_by_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('Person:', col[@field='Approved By'])"/>
                            </xsl:attribute>
                        </reference>
<!--                        <reference field="approved_by_id" resource="hrm_human_resource">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('HR:', col[@field='Approved By'])"/>
                            </xsl:attribute>
                        </reference>-->
                    </xsl:if>
                    <xsl:if test="col[@field='Received By']!=''">
                        <reference field="recv_by_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('Person:', col[@field='Received By'])"/>
                            </xsl:attribute>
                        </reference>
<!--                        <reference field="recv_by_id" resource="hrm_human_resource">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('HR:', col[@field='Received By'])"/>
                            </xsl:attribute>
                        </reference>-->
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="col[@field='Requester']!=''">
                <reference field="requester_id" resource="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Person:', col[@field='Requester'])"/>
                    </xsl:attribute>
                </reference>
<!--                <reference field="requester_id" resource="hrm_human_resource">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('HR:', col[@field='Requester'])"/>
                    </xsl:attribute>
                </reference>-->
            </xsl:if>
            <xsl:if test="col[@field='Assigned To']!=''">
                <reference field="assigned_to_id" resource="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Person:', col[@field='Assigned To'])"/>
                    </xsl:attribute>
                </reference>
<!--                <reference field="assigned_to_id" resource="hrm_human_resource">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('HR:', col[@field='Assigned To'])"/>
                    </xsl:attribute>
                </reference>-->
            </xsl:if>
            <xsl:if test="col[@field='Requested For']!=''">
                <reference field="request_for_id" resource="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Person:', col[@field='Requested For'])"/>
                    </xsl:attribute>
                </reference>
<!--                <reference field="request_for_id" resource="hrm_human_resource">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('HR:', col[@field='Requested For'])"/>
                    </xsl:attribute>
                </reference>-->
            </xsl:if>
            <data field="purpose"><xsl:value-of select="col[@field='Purpose']"/></data>
            <data field="transport_req"><xsl:value-of select="col[@field='Transportation Required']"/></data>
            <data field="security_req"><xsl:value-of select="col[@field='Security Required']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            <!-- Arbitrary Tags -->
            <xsl:for-each select="col[starts-with(@field, 'KV')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="req_req_tag" alias="tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Scenario">

        <xsl:variable name="Scenario" select="col[@field='Scenario']"/>

        <xsl:if test="$Scenario!=''">
            <resource name="scenario_scenario">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Scenario:', $Scenario)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Scenario"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Event">

        <xsl:variable name="Event" select="col[@field='Event']"/>
        <xsl:variable name="Scenario" select="col[@field='Scenario']"/>

        <xsl:if test="$Event!=''">
            <resource name="event_event">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Event:', $Event)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Event"/></data>
                <xsl:if test="$Scenario!=''">
                    <reference field="scenario_id" resource="scenario_scenario">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Scenario:', $Scenario)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Facility">

        <xsl:variable name="FacilityName" select="col[@field='Requested for Facility']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Requested for Facility Type']/text()"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>inv_warehouse</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <resource>
            <xsl:attribute name="name">
                <xsl:value-of select="$resourcename"/>
            </xsl:attribute>
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Facility:', $FacilityName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$FacilityName"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="HumanResource">
        <xsl:param name="Name"/>

        <xsl:if test="$Name!=''">
            <xsl:variable name="FirstName"  select="substring-before($Name,' ')"/>
            <xsl:variable name="LastName"  select="substring-after($Name,' ')"/>
            <!-- Person record -->
            <resource name="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Person:', $Name)"/>
                </xsl:attribute>
                <data field="first_name">
                    <xsl:value-of select="$FirstName"/>
                </data>
                <data field="last_name">
                    <xsl:value-of select="$LastName"/>
                </data>
            </resource>
            <!-- HR -->
            <resource name="hrm_human_resource">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('HR:', $Name)"/>
                </xsl:attribute>
                <reference field="person_id" resource="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Person:', $Name)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
